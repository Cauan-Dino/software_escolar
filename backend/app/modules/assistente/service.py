"""Regras do assistente: conversas, loop de tool calling e confirmação de ações.

Garantias centrais:
- O modelo só PROPÕE ações de escrita. Elas viram `AcaoPendente` e só executam em
  `confirmar_acao`, chamada por um endpoint autenticado quando o usuário clica no botão.
- Tudo roda com a identidade do usuário logado (`CurrentUser`).
- O texto do cartão de confirmação vem do servidor (preview montado a partir do banco).
"""

import json
import logging
import uuid
from datetime import timedelta
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.modules.assistente import prompts, repository, tools
from app.modules.assistente.llm import LLMClient, LLMResponse, ToolCall, build_default_client
from app.modules.assistente.models import AcaoPendente, Conversa, Mensagem, StatusAcao
from app.modules.assistente.schemas import (
    AcaoRead,
    ConversaDetalhe,
    ConversaRead,
    DecisaoAcao,
    MensagemRead,
    RespostaChat,
)
from app.modules.assistente.tools import ToolContext
from app.shared import clock

logger = logging.getLogger(__name__)

TITULO_PADRAO = "Nova conversa"
MAX_CHARS_RESULTADO = 6000
CONVERSA_NAO_ENCONTRADA = "Conversa não encontrada."
ACAO_NAO_ENCONTRADA = "Ação não encontrada."


def get_llm_client() -> LLMClient:
    """Dependency do router (os testes sobrescrevem por um cliente falso)."""
    return build_default_client()


# --- Conversas -----------------------------------------------------------------------------


def _get_conversa_or_404(db: Session, conversa_id: int, user: CurrentUser) -> Conversa:
    conversa = repository.get_conversa(db, conversa_id, user.id)
    if conversa is None:
        raise NotFoundError(CONVERSA_NAO_ENCONTRADA)
    return conversa


def create_conversa(db: Session, user: CurrentUser) -> ConversaRead:
    conversa = Conversa(user_id=user.id, titulo=TITULO_PADRAO)
    repository.add(db, conversa)
    db.commit()
    return ConversaRead.model_validate(conversa)


def list_conversas(db: Session, user: CurrentUser) -> list[ConversaRead]:
    return [ConversaRead.model_validate(c) for c in repository.list_conversas(db, user.id)]


def delete_conversa(db: Session, conversa_id: int, user: CurrentUser) -> None:
    conversa = _get_conversa_or_404(db, conversa_id, user)
    repository.delete_conversa(db, conversa)
    db.commit()


def get_conversa(db: Session, conversa_id: int, user: CurrentUser) -> ConversaDetalhe:
    conversa = _get_conversa_or_404(db, conversa_id, user)
    _expirar_vencidas(db, conversa.id)
    mensagens = repository.list_mensagens(db, conversa.id)
    return ConversaDetalhe(
        id=conversa.id,
        titulo=conversa.titulo,
        created_at=conversa.created_at,
        updated_at=conversa.updated_at,
        mensagens=_visiveis(db, conversa.id, mensagens),
    )


# --- Conversão para o que o usuário vê --------------------------------------------------------


def _titulo_da_ferramenta(nome: str) -> str:
    tool = tools.get_tool(nome)
    return tool.titulo if tool else nome


def _acao_read(acao: AcaoPendente) -> AcaoRead:
    return AcaoRead(
        id=acao.id,
        ferramenta=acao.ferramenta,
        titulo=_titulo_da_ferramenta(acao.ferramenta),
        resumo=acao.resumo,
        destrutiva=acao.destrutiva,
        status=acao.status,
        expira_em=acao.expira_em,
        decidida_em=acao.decidida_em,
        resultado=acao.resultado,
        erro=acao.erro,
    )


def _visiveis(db: Session, conversa_id: int, mensagens: list[Mensagem]) -> list[MensagemRead]:
    """Mensagens que o usuário enxerga: texto dele, texto do assistente e cartões de ação."""
    acoes = {a.id: a for a in repository.list_acoes_da_conversa(db, conversa_id)}
    resultado: list[MensagemRead] = []
    for m in mensagens:
        if m.role == "user" or (m.role == "assistant" and m.conteudo):
            resultado.append(
                MensagemRead(id=m.id, role=m.role, conteudo=m.conteudo, created_at=m.created_at)
            )
        elif m.role == "tool" and m.acao_id and m.acao_id in acoes:
            acao = acoes[m.acao_id]
            resultado.append(
                MensagemRead(
                    id=m.id,
                    role="acao",
                    conteudo=acao.resumo,
                    created_at=m.created_at,
                    acao=_acao_read(acao),
                )
            )
    return resultado


# --- Histórico enviado ao LLM -----------------------------------------------------------------


def _para_llm(m: Mensagem) -> dict[str, Any]:
    if m.role == "assistant":
        msg: dict[str, Any] = {"role": "assistant", "content": m.conteudo}
        if m.tool_calls:
            msg["tool_calls"] = m.tool_calls
        return msg
    if m.role == "tool":
        return {"role": "tool", "tool_call_id": m.tool_call_id, "content": m.conteudo or ""}
    return {"role": "user", "content": m.conteudo or ""}


def _janela(mensagens: list[Mensagem]) -> list[Mensagem]:
    """Últimas N mensagens, sempre começando numa mensagem do usuário (sem `tool` órfã)."""
    limite = settings.assistente_historico_max_mensagens
    inicio = max(len(mensagens) - limite, 0)
    for i in range(inicio, len(mensagens)):
        if mensagens[i].role == "user":
            return mensagens[i:]
    for i in range(len(mensagens) - 1, -1, -1):
        if mensagens[i].role == "user":
            return mensagens[i:]
    return mensagens


def _montar_historico(db: Session, conversa: Conversa, user: CurrentUser) -> list[dict[str, Any]]:
    mensagens = _janela(repository.list_mensagens(db, conversa.id))
    return [{"role": "system", "content": prompts.system_prompt(user)}] + [
        _para_llm(m) for m in mensagens
    ]


# --- Execução das chamadas de ferramenta -------------------------------------------------------


def _erro_json(mensagem: str, code: str = "ERRO") -> str:
    return json.dumps({"erro": mensagem, "code": code}, ensure_ascii=False)


def _texto_resultado(valor: Any) -> str:
    texto = json.dumps(valor, ensure_ascii=False, default=str)
    if len(texto) > MAX_CHARS_RESULTADO:
        texto = texto[:MAX_CHARS_RESULTADO] + "… [resultado truncado: refine a busca]"
    return texto


def _resumo_erros(exc: ValidationError) -> str:
    partes = []
    for erro in exc.errors()[:5]:
        campo = ".".join(str(p) for p in erro["loc"]) or "argumentos"
        partes.append(f"{campo}: {erro['msg']}")
    return "; ".join(partes)


def _executar_chamada(
    db: Session, conversa: Conversa, user: CurrentUser, call: ToolCall
) -> tuple[str, str | None]:
    """Executa (leitura) ou prepara (escrita) uma chamada. Devolve (texto p/ o modelo, acao_id)."""
    tool = tools.get_tool(call.name)
    if tool is None or user.role not in tool.roles:
        return _erro_json(
            "Ferramenta indisponível para este usuário.", "FERRAMENTA_INDISPONIVEL"
        ), None
    try:
        args = tool.input_model.model_validate_json(call.arguments or "{}")
    except ValidationError as exc:
        return _erro_json(
            f"Argumentos inválidos: {_resumo_erros(exc)}", "ARGUMENTOS_INVALIDOS"
        ), None

    ctx = ToolContext(db=db, user=user)
    try:
        if not tool.mutates:
            return _texto_resultado(tools.serializar(tool.handler(ctx, args))), None

        assert tool.preview is not None  # noqa: S101
        resumo = tool.preview(ctx, args)
        acao = AcaoPendente(
            id=str(uuid.uuid4()),
            conversa_id=conversa.id,
            user_id=user.id,
            ferramenta=tool.name,
            argumentos=args.model_dump(mode="json", exclude_unset=True),
            resumo=resumo,
            destrutiva=tool.destrutiva,
            status=StatusAcao.PENDENTE,
            expira_em=clock.now() + timedelta(minutes=settings.assistente_acao_expira_minutos),
        )
        repository.add(db, acao)
        db.commit()
        aviso = {
            "status": "AGUARDANDO_CONFIRMACAO",
            "mensagem": (
                "A ação foi preparada e mostrada ao usuário com botões Confirmar/Cancelar. "
                "Ela AINDA NÃO foi executada. Avise que está aguardando a confirmação."
            ),
        }
        return json.dumps(aviso, ensure_ascii=False), acao.id
    except AppError as exc:
        db.rollback()
        return _erro_json(exc.detail, exc.code), None
    except Exception:
        logger.exception("Falha inesperada na ferramenta %s", tool.name)
        db.rollback()
        return _erro_json("Erro interno ao executar a ferramenta.", "ERRO_INTERNO"), None


def _add_mensagem(db: Session, conversa: Conversa, **campos: Any) -> Mensagem:
    mensagem = Mensagem(conversa_id=conversa.id, **campos)
    repository.add(db, mensagem)
    return mensagem


def _tool_calls_para_historico(calls: list[ToolCall]) -> list[dict[str, Any]]:
    return [
        {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
        for c in calls
    ]


# --- Envio de mensagem (loop do agente) -------------------------------------------------------


def enviar_mensagem(
    db: Session, conversa_id: int, texto: str, user: CurrentUser, llm_client: LLMClient
) -> RespostaChat:
    conversa = _get_conversa_or_404(db, conversa_id, user)
    _expirar_vencidas(db, conversa.id)

    novas: list[Mensagem] = [_add_mensagem(db, conversa, role="user", conteudo=texto)]
    if conversa.titulo == TITULO_PADRAO:
        conversa.titulo = texto[:60]
    conversa.updated_at = clock.now()
    db.commit()

    for _ in range(settings.assistente_max_passos):
        historico = _montar_historico(db, conversa, user)
        resposta: LLMResponse = llm_client.chat(historico, tools.specs_for_role(user.role))

        if not resposta.tool_calls:
            conteudo = resposta.content or "Não consegui gerar uma resposta. Pode reformular?"
            novas.append(_add_mensagem(db, conversa, role="assistant", conteudo=conteudo))
            db.commit()
            break

        novas.append(
            _add_mensagem(
                db,
                conversa,
                role="assistant",
                conteudo=resposta.content,
                tool_calls=_tool_calls_para_historico(resposta.tool_calls),
            )
        )
        db.commit()

        criou_acao = False
        for call in resposta.tool_calls:
            texto_resultado, acao_id = _executar_chamada(db, conversa, user, call)
            novas.append(
                _add_mensagem(
                    db,
                    conversa,
                    role="tool",
                    tool_call_id=call.id,
                    conteudo=texto_resultado,
                    acao_id=acao_id,
                )
            )
            db.commit()
            criou_acao = criou_acao or acao_id is not None

        if criou_acao:
            # Para aqui: o usuário precisa decidir (botões) antes de o agente continuar.
            if not resposta.content:
                novas.append(
                    _add_mensagem(
                        db,
                        conversa,
                        role="assistant",
                        conteudo="Preparei a ação abaixo. Confirme para eu executar.",
                    )
                )
                db.commit()
            break
    else:
        novas.append(
            _add_mensagem(
                db,
                conversa,
                role="assistant",
                conteudo="Não consegui concluir o pedido. Pode reformulá-lo de outra forma?",
            )
        )
        db.commit()

    return RespostaChat(conversa_id=conversa.id, mensagens=_visiveis(db, conversa.id, novas))


# --- Confirmação / cancelamento ---------------------------------------------------------------


def _expirar_vencidas(db: Session, conversa_id: int) -> None:
    vencidas = repository.list_acoes_pendentes_vencidas(db, conversa_id, clock.now())
    for acao in vencidas:
        acao.status = StatusAcao.EXPIRADA
        acao.decidida_em = clock.now()
    if vencidas:
        db.commit()


def _carregar_acao_pendente(db: Session, acao_id: str, user: CurrentUser) -> AcaoPendente:
    acao = repository.get_acao(db, acao_id, user.id, for_update=True)
    if acao is None:
        raise NotFoundError(ACAO_NAO_ENCONTRADA)
    if acao.status == StatusAcao.PENDENTE and acao.expira_em <= clock.now():
        acao.status = StatusAcao.EXPIRADA
        acao.decidida_em = clock.now()
        db.commit()
    if acao.status != StatusAcao.PENDENTE:
        raise ConflictError(
            f"Esta ação não está mais pendente (status: {acao.status.value}).", "ACAO_NAO_PENDENTE"
        )
    return acao


def _mensagem_final(db: Session, acao: AcaoPendente, texto: str) -> list[MensagemRead]:
    conversa = db.get(Conversa, acao.conversa_id)
    assert conversa is not None  # noqa: S101
    mensagem = _add_mensagem(db, conversa, role="assistant", conteudo=texto)
    conversa.updated_at = clock.now()
    db.commit()
    return _visiveis(db, conversa.id, [mensagem])


def confirmar_acao(db: Session, acao_id: str, user: CurrentUser) -> DecisaoAcao:
    acao = _carregar_acao_pendente(db, acao_id, user)
    tool = tools.get_tool(acao.ferramenta)
    if tool is None or user.role not in tool.roles:
        raise ForbiddenError("Você não tem permissão para executar esta ação.")
    titulo = tool.titulo
    ferramenta = acao.ferramenta
    argumentos = acao.argumentos

    # Marca como confirmada na MESMA transação do efeito de negócio: o commit do service
    # grava os dois juntos, então um clique nunca executa duas vezes.
    acao.status = StatusAcao.CONFIRMADA
    acao.decidida_em = clock.now()
    db.flush()
    record_audit(
        db,
        actor=user,
        action=f"assistente.{ferramenta}",
        entity="assistente_acao",
        entity_id=acao.id,
        after={"ferramenta": ferramenta, "argumentos": argumentos},
    )
    try:
        args = tool.input_model.model_validate(argumentos)
        valor = tool.handler(ToolContext(db=db, user=user), args)
        resultado = tools.como_resultado(valor)
        acao.resultado = resultado
        db.commit()
    except (AppError, ValidationError) as exc:
        db.rollback()
        detalhe = exc.detail if isinstance(exc, AppError) else _resumo_erros(exc)
        return _registrar_falha(db, acao_id, user, titulo, detalhe)
    except Exception:
        logger.exception("Falha inesperada ao confirmar a ação %s", acao_id)
        db.rollback()
        return _registrar_falha(db, acao_id, user, titulo, "Erro interno ao executar a ação.")

    ref = f" (id {resultado['id']})" if isinstance(resultado.get("id"), int) else ""
    mensagens = _mensagem_final(db, acao, f"✅ Pronto! {titulo} executada com sucesso{ref}.")
    return DecisaoAcao(acao=_acao_read(acao), mensagens=mensagens)


def _registrar_falha(
    db: Session, acao_id: str, user: CurrentUser, titulo: str, detalhe: str
) -> DecisaoAcao:
    acao = repository.get_acao(db, acao_id, user.id, for_update=True)
    assert acao is not None  # noqa: S101
    acao.status = StatusAcao.FALHOU
    acao.erro = detalhe
    acao.decidida_em = clock.now()
    db.commit()
    mensagens = _mensagem_final(db, acao, f"⚠️ Não consegui executar «{titulo}». Motivo: {detalhe}")
    return DecisaoAcao(acao=_acao_read(acao), mensagens=mensagens)


def cancelar_acao(db: Session, acao_id: str, user: CurrentUser) -> DecisaoAcao:
    acao = _carregar_acao_pendente(db, acao_id, user)
    acao.status = StatusAcao.CANCELADA
    acao.decidida_em = clock.now()
    db.commit()
    titulo = _titulo_da_ferramenta(acao.ferramenta)
    mensagens = _mensagem_final(db, acao, f"Ação cancelada: {titulo}. Nada foi alterado.")
    return DecisaoAcao(acao=_acao_read(acao), mensagens=mensagens)
