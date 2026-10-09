"""Registro das ferramentas (tool calling) do assistente.

Cada `Tool` descreve: nome, descrição para o modelo, schema de entrada (Pydantic), perfis que
podem usá-la, se ALTERA dados (`mutates`) e o handler que chama o service do módulo de negócio.

Regras:
- Ferramentas de escrita (`mutates=True`) NUNCA são executadas pelo loop do agente: viram uma
  ação pendente e só rodam quando o usuário clica em Confirmar (ver `service.confirmar_acao`).
- Toda escrita tem um `preview`, que gera o texto do cartão de confirmação A PARTIR DO BANCO
  (nomes reais), não do texto do modelo; se o preview falhar (id inexistente, sem acesso), a
  proposta é recusada e o modelo recebe o erro.
- Os handlers chamam o `service` de cada módulo com o `CurrentUser` real: valem os mesmos
  vínculos e regras de negócio da API. Como os services não checam perfil (quem checa é o
  router), os perfis são reaplicados aqui em `roles` e validados por teste de paridade.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import NotFoundError
from app.core.roles import Role
from app.modules.assistente import permissions as perm
from app.modules.assistente import prompts
from app.modules.assistente import schemas as s
from app.modules.calendario import service as calendario_service
from app.modules.calendario.schemas import EventoCalendarioUpdate
from app.modules.comunicacao import service as comunicacao_service
from app.modules.comunicacao.schemas import AvisoUpdate
from app.modules.financeiro import service as financeiro_service
from app.modules.financeiro.schemas import BolsaUpdate, TabelaPrecoUpdate
from app.modules.frequencia import service as frequencia_service
from app.modules.frequencia.schemas import CorrigirRegistro, LancarChamada
from app.modules.matricula import service as matricula_service
from app.modules.matricula.schemas import (
    DOCUMENTO_LABELS,
    AprovarMatricula,
    DocumentoCheck,
    MotivoInput,
)
from app.modules.notas import service as notas_service
from app.modules.notas.schemas import PERIODO_LABELS, NotaUpsert
from app.modules.pessoas import service as pessoas_service
from app.modules.pessoas.schemas import (
    AlunoCreate,
    AlunoUpdate,
    ResponsavelCreate,
    ResponsavelUpdate,
    VinculoCreate,
    VinculoUpdate,
)
from app.modules.turmas import service as turmas_service
from app.modules.turmas.schemas import TurmaCreate, TurmaUpdate
from app.shared import clock
from app.shared.serie import Serie


@dataclass(frozen=True)
class ToolContext:
    db: Session
    user: CurrentUser


Handler = Callable[[ToolContext, Any], Any]
Preview = Callable[[ToolContext, Any], str]


@dataclass(frozen=True)
class Tool:
    name: str
    titulo: str
    description: str
    input_model: type[BaseModel]
    roles: tuple[Role, ...]
    handler: Handler
    mutates: bool = False
    destrutiva: bool = False
    preview: Preview | None = None

    def spec(self) -> dict[str, Any]:
        """Definição no formato `tools` da API compatível com OpenAI."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": clean_schema(self.input_model.model_json_schema()),
            },
        }


# --- JSON Schema enxuto -----------------------------------------------------------------------


def clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve `$ref`/`$defs`, remove `title` e simplifica `anyOf: [X, null]` para o modelo."""
    defs = schema.get("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, list):
            return [resolve(n) for n in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            alvo = defs[node["$ref"].split("/")[-1]]
            extra = {k: v for k, v in node.items() if k != "$ref"}
            return resolve({**alvo, **extra})
        if "anyOf" in node:
            opcoes = [o for o in node["anyOf"] if o.get("type") != "null"]
            if len(opcoes) == 1:
                resto = {k: v for k, v in node.items() if k not in ("anyOf", "default")}
                return resolve({**opcoes[0], **resto})
        limpo = {k: resolve(v) for k, v in node.items() if k not in ("title", "$defs")}
        return limpo

    resultado = resolve({k: v for k, v in schema.items() if k != "$defs"})
    resultado.setdefault("type", "object")
    resultado.setdefault("properties", {})
    return resultado


# --- Serialização do resultado das ferramentas -----------------------------------------------

_OCULTAR = frozenset(
    {
        "cpf",
        "user_id",
        "password_hash",
        "criado_por_user_id",
        "lancado_por_user_id",
        "publicado_por_user_id",
        "decidido_por_user_id",
        "conferido_por_user_id",
    }
)


def _limpar(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {k: _limpar(v) for k, v in valor.items() if k not in _OCULTAR}
    if isinstance(valor, list):
        return [_limpar(v) for v in valor]
    return valor


def serializar(valor: Any) -> Any:
    """Converte o retorno de um service em JSON simples, sem campos sensíveis (CPF, user ids)."""
    if isinstance(valor, BaseModel):
        valor = valor.model_dump(mode="json")
    elif isinstance(valor, list):
        valor = [v.model_dump(mode="json") if isinstance(v, BaseModel) else v for v in valor]
    return _limpar(valor)


def como_resultado(valor: Any) -> dict[str, Any]:
    """Resultado de uma escrita, sempre como objeto JSON."""
    dados = serializar(valor)
    if dados is None:
        return {"ok": True}
    if isinstance(dados, list):
        return {"itens": dados}
    if isinstance(dados, dict):
        return dados
    return {"valor": dados}


# --- Formatação do texto de confirmação ------------------------------------------------------


def _fmt(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, Decimal):
        return f"R$ {valor:.2f}".replace(".", ",")
    if isinstance(valor, Serie):
        return valor.label
    if isinstance(valor, Enum):
        return str(valor.value)
    return str(valor)


def _bloco(titulo: str, *pares: tuple[str, Any]) -> str:
    linhas = [titulo]
    linhas.extend(f"• {rotulo}: {_fmt(valor)}" for rotulo, valor in pares)
    return "\n".join(linhas)


def _mudancas(dados: BaseModel, ignorar: set[str]) -> list[tuple[str, Any]]:
    campos = dados.model_dump(exclude_unset=True, exclude=ignorar)
    return [(nome.replace("_", " ").capitalize(), valor) for nome, valor in campos.items()]


# --- Resolução de entidades (levantam 404/403 se não existir ou sem acesso) ---------------------


def _aluno(ctx: ToolContext, aluno_id: int) -> str:
    """Nome do aluno. Responsável/aluno só enxergam os vinculados; equipe e professor, qualquer
    um (o professor lança notas/frequência de alunos da própria turma)."""
    if ctx.user.role in (Role.RESPONSAVEL, Role.ALUNO):
        aluno = pessoas_service.get_aluno(ctx.db, aluno_id, ctx.user)
    else:
        aluno = pessoas_service.get_aluno_read(ctx.db, aluno_id)
    return f"{aluno.nome} (id {aluno.id})"


def _responsavel(ctx: ToolContext, responsavel_id: int) -> str:
    resp = pessoas_service.get_responsavel(ctx.db, responsavel_id)
    return f"{resp.nome} (id {resp.id})"


def _professor(ctx: ToolContext, professor_id: int) -> str:
    prof = pessoas_service.get_professor(ctx.db, professor_id)
    return f"{prof.nome} (id {prof.id})"


def _turma(ctx: ToolContext, turma_id: int) -> str:
    turma = turmas_service.get_turma(ctx.db, turma_id, ctx.user)
    return f"{turma.nome} (id {turma.id})"


def _matricula(ctx: ToolContext, matricula_id: int) -> str:
    m = matricula_service.get_matricula(ctx.db, matricula_id, ctx.user)
    return (
        f"matrícula #{m.id} de {m.aluno_nome} — {m.serie.label}/{m.ano_letivo}, "
        f"status {m.status.value}"
    )


# =============================================================================================
# HANDLERS DE LEITURA
# =============================================================================================


def _quem_sou_eu(ctx: ToolContext, _: s.SemArgumentos) -> dict[str, Any]:
    dados: dict[str, Any] = {
        "email": ctx.user.email,
        "perfil": ctx.user.role.value,
        "hoje": clock.today().isoformat(),
    }
    if ctx.user.role == Role.RESPONSAVEL:
        dados["alunos"] = [
            {"id": a.id, "nome": a.nome} for a in pessoas_service.list_meus_alunos(ctx.db, ctx.user)
        ]
    elif ctx.user.role == Role.ALUNO:
        aluno = pessoas_service.get_aluno_by_user(ctx.db, ctx.user.id)
        dados["aluno"] = {"id": aluno.id, "nome": aluno.nome} if aluno else None
    elif ctx.user.role == Role.PROFESSOR:
        prof = pessoas_service.get_professor_by_user(ctx.db, ctx.user.id)
        dados["professor"] = {"id": prof.id, "nome": prof.nome} if prof else None
    return dados


def _consultar_ajuda(_: ToolContext, a: s.AjudaInput) -> dict[str, Any]:
    secoes = prompts.buscar_ajuda(a.topico)
    if not secoes:
        return {
            "resultado": "Nada encontrado para esse tópico.",
            "topicos_disponiveis": list(prompts.CONHECIMENTO),
        }
    return {"secoes": [{"titulo": t, "conteudo": c} for t, c in secoes]}


def _buscar_alunos(ctx: ToolContext, a: s.BuscaInput) -> Any:
    return pessoas_service.list_alunos(ctx.db, busca=a.busca, limit=a.limite, offset=0)


def _obter_aluno(ctx: ToolContext, a: s.AlunoIdInput) -> Any:
    return pessoas_service.get_aluno(ctx.db, a.aluno_id, ctx.user)


def _listar_meus_alunos(ctx: ToolContext, _: s.SemArgumentos) -> Any:
    return pessoas_service.list_meus_alunos(ctx.db, ctx.user)


def _obter_meu_cadastro(ctx: ToolContext, _: s.SemArgumentos) -> Any:
    aluno = pessoas_service.get_aluno_by_user(ctx.db, ctx.user.id)
    if aluno is None:
        raise NotFoundError("Aluno não encontrado.")
    return aluno


def _buscar_responsaveis(ctx: ToolContext, a: s.BuscaInput) -> Any:
    return pessoas_service.list_responsaveis(ctx.db, busca=a.busca, limit=a.limite, offset=0)


def _obter_responsavel(ctx: ToolContext, a: s.ResponsavelIdInput) -> Any:
    return pessoas_service.get_responsavel(ctx.db, a.responsavel_id)


def _buscar_professores(ctx: ToolContext, a: s.BuscaInput) -> Any:
    return pessoas_service.list_professores(ctx.db, busca=a.busca, limit=a.limite, offset=0)


def _listar_turmas(ctx: ToolContext, a: s.ListarTurmasInput) -> Any:
    return turmas_service.list_turmas(ctx.db, ano_letivo=a.ano_letivo, serie=a.serie, ativa=a.ativa)


def _obter_turma(ctx: ToolContext, a: s.TurmaIdInput) -> Any:
    return turmas_service.get_turma(ctx.db, a.turma_id, ctx.user)


def _listar_minhas_turmas(ctx: ToolContext, _: s.SemArgumentos) -> Any:
    return turmas_service.list_minhas_turmas(ctx.db, ctx.user)


def _listar_matriculas(ctx: ToolContext, a: s.ListarMatriculasInput) -> Any:
    return matricula_service.list_matriculas(
        ctx.db,
        ctx.user,
        status=a.status,
        ano_letivo=a.ano_letivo,
        serie=a.serie,
        limit=a.limite,
        offset=0,
    )


def _obter_matricula(ctx: ToolContext, a: s.MatriculaIdInput) -> Any:
    return matricula_service.get_matricula(ctx.db, a.matricula_id, ctx.user)


def _listar_disciplinas(_: ToolContext, __: s.SemArgumentos) -> Any:
    return {"disciplinas": notas_service.list_disciplinas()}


def _obter_boletim(ctx: ToolContext, a: s.AlunoIdInput) -> Any:
    return notas_service.get_boletim(ctx.db, a.aluno_id, ctx.user)


def _ver_grade_notas(ctx: ToolContext, a: s.GradeNotasInput) -> dict[str, Any]:
    grade = notas_service.list_grade(ctx.db, a.turma_id, a.periodo, ctx.user)
    por_aluno: dict[int, dict[str, Any]] = {}
    for celula in grade.celulas:
        item = por_aluno.setdefault(
            celula.aluno_id,
            {"aluno_id": celula.aluno_id, "aluno": celula.aluno_nome, "notas": {}},
        )
        if celula.valor is not None:
            item["notas"][celula.disciplina] = celula.valor
    return {
        "turma_id": grade.turma_id,
        "periodo": grade.periodo.value,
        "alunos": list(por_aluno.values()),
    }


def _ver_chamada(ctx: ToolContext, a: s.ChamadaDiaInput) -> Any:
    return frequencia_service.get_chamada_do_dia(
        ctx.db, a.turma_id, a.data or clock.today(), ctx.user
    )


def _ver_frequencia_aluno(ctx: ToolContext, a: s.HistoricoFrequenciaInput) -> Any:
    ate = a.ate or clock.today()
    de = a.de or (ate - timedelta(days=30))
    return frequencia_service.get_historico_do_aluno(ctx.db, a.aluno_id, de, ate, ctx.user)


def _listar_cobrancas(ctx: ToolContext, a: s.ListarCobrancasInput) -> Any:
    """Mesmo escopo do router: responsável/aluno só enxergam o que é deles."""
    aluno_ids: list[int] | None = None
    aluno_id = a.aluno_id
    if ctx.user.role == Role.RESPONSAVEL:
        if aluno_id is not None:
            pessoas_service.ensure_can_access_aluno(ctx.db, ctx.user, aluno_id)
        else:
            aluno_ids = pessoas_service.list_aluno_ids_do_usuario(ctx.db, ctx.user)
    elif ctx.user.role == Role.ALUNO:
        meu = pessoas_service.get_aluno_by_user(ctx.db, ctx.user.id)
        meu_id = meu.id if meu else None
        if aluno_id is not None:
            if meu_id is None or aluno_id != meu_id:
                raise NotFoundError("Aluno não encontrado.")
        else:
            aluno_ids = [meu_id] if meu_id is not None else []
    return financeiro_service.list_cobrancas(
        ctx.db, aluno_id=aluno_id, aluno_ids=aluno_ids, status=a.status, limit=a.limite, offset=0
    )


def _verificar_inadimplencia(ctx: ToolContext, a: s.AlunoIdInput) -> dict[str, Any]:
    pessoas_service.get_aluno_read(ctx.db, a.aluno_id)
    return {
        "aluno_id": a.aluno_id,
        "inadimplente": financeiro_service.is_aluno_inadimplente(ctx.db, a.aluno_id),
    }


def _listar_bolsas(ctx: ToolContext, a: s.ListarBolsasInput) -> Any:
    return financeiro_service.list_bolsas(ctx.db, aluno_id=a.aluno_id)


def _listar_precos(ctx: ToolContext, _: s.SemArgumentos) -> Any:
    return financeiro_service.list_precos(ctx.db)


def _listar_eventos(ctx: ToolContext, a: s.ListarEventosInput) -> Any:
    de = a.de or clock.today()
    ate = a.ate or (de + timedelta(days=60))
    return calendario_service.list_eventos(ctx.db, de=de, ate=ate, turma_id=a.turma_id)


def _listar_avisos(ctx: ToolContext, a: s.LimiteInput) -> Any:
    return comunicacao_service.list_avisos(ctx.db, ctx.user, limit=a.limite, offset=0)


def _contar_avisos_nao_lidos(ctx: ToolContext, _: s.SemArgumentos) -> Any:
    return comunicacao_service.contar_nao_lidos(ctx.db, ctx.user)


# =============================================================================================
# HANDLERS DE ESCRITA (só executados após confirmação)
# =============================================================================================


def _criar_aluno(ctx: ToolContext, a: AlunoCreate) -> Any:
    return pessoas_service.create_aluno(ctx.db, a)


def _atualizar_aluno(ctx: ToolContext, a: s.AtualizarAlunoInput) -> Any:
    dados = AlunoUpdate(**a.model_dump(exclude_unset=True, exclude={"aluno_id"}))
    return pessoas_service.update_aluno(ctx.db, a.aluno_id, dados)


def _excluir_aluno(ctx: ToolContext, a: s.AlunoIdInput) -> Any:
    return pessoas_service.delete_aluno(ctx.db, a.aluno_id)


def _vincular_responsavel(ctx: ToolContext, a: s.VincularResponsavelInput) -> Any:
    dados = VinculoCreate(**a.model_dump(exclude={"aluno_id"}))
    return pessoas_service.add_vinculo(ctx.db, a.aluno_id, dados)


def _atualizar_vinculo(ctx: ToolContext, a: s.AtualizarVinculoInput) -> Any:
    dados = VinculoUpdate(
        **a.model_dump(exclude_unset=True, exclude={"aluno_id", "responsavel_id"})
    )
    return pessoas_service.update_vinculo(ctx.db, a.aluno_id, a.responsavel_id, dados)


def _remover_vinculo(ctx: ToolContext, a: s.RemoverVinculoInput) -> Any:
    return pessoas_service.remove_vinculo(ctx.db, a.aluno_id, a.responsavel_id)


def _criar_responsavel(ctx: ToolContext, a: s.CriarResponsavelInput) -> Any:
    return pessoas_service.create_responsavel(ctx.db, ResponsavelCreate(**a.model_dump()))


def _atualizar_responsavel(ctx: ToolContext, a: s.AtualizarResponsavelInput) -> Any:
    dados = ResponsavelUpdate(**a.model_dump(exclude_unset=True, exclude={"responsavel_id"}))
    return pessoas_service.update_responsavel(ctx.db, a.responsavel_id, dados)


def _criar_turma(ctx: ToolContext, a: TurmaCreate) -> Any:
    return turmas_service.create_turma(ctx.db, a)


def _atualizar_turma(ctx: ToolContext, a: s.AtualizarTurmaInput) -> Any:
    dados = TurmaUpdate(**a.model_dump(exclude_unset=True, exclude={"turma_id"}))
    return turmas_service.update_turma(ctx.db, a.turma_id, dados)


def _adicionar_professor(ctx: ToolContext, a: s.ProfessorTurmaInput) -> Any:
    return turmas_service.add_professor(ctx.db, a.turma_id, a.professor_id)


def _remover_professor(ctx: ToolContext, a: s.ProfessorTurmaInput) -> Any:
    return turmas_service.remove_professor(ctx.db, a.turma_id, a.professor_id)


def _criar_pre_matricula(ctx: ToolContext, a: s.CriarPreMatriculaInput) -> Any:
    return matricula_service.create_pre_matricula(ctx.db, a, ctx.user)


def _iniciar_analise(ctx: ToolContext, a: s.MatriculaIdInput) -> Any:
    return matricula_service.start_analise(ctx.db, a.matricula_id, ctx.user)


def _aprovar_matricula(ctx: ToolContext, a: s.AprovarMatriculaInput) -> Any:
    return matricula_service.approve_matricula(
        ctx.db, a.matricula_id, AprovarMatricula(turma_id=a.turma_id), ctx.user
    )


def _rejeitar_matricula(ctx: ToolContext, a: s.MotivoMatriculaInput) -> Any:
    return matricula_service.reject_matricula(
        ctx.db, a.matricula_id, MotivoInput(motivo=a.motivo), ctx.user
    )


def _cancelar_matricula(ctx: ToolContext, a: s.MotivoMatriculaInput) -> Any:
    return matricula_service.cancel_matricula(
        ctx.db, a.matricula_id, MotivoInput(motivo=a.motivo), ctx.user
    )


def _marcar_documento(ctx: ToolContext, a: s.DocumentoMatriculaInput) -> Any:
    return matricula_service.check_documento(
        ctx.db, a.matricula_id, a.tipo, DocumentoCheck(entregue=a.entregue), ctx.user
    )


def _lancar_nota(ctx: ToolContext, a: s.LancarNotaInput) -> Any:
    dados = NotaUpsert(
        disciplina=a.disciplina, periodo=a.periodo, valor=a.valor, observacao=a.observacao
    )
    return notas_service.upsert_nota(ctx.db, a.turma_id, a.aluno_id, dados, ctx.user)


def _lancar_chamada(ctx: ToolContext, a: s.LancarChamadaInput) -> Any:
    return frequencia_service.lancar_chamada(
        ctx.db, a.turma_id, a.data or clock.today(), LancarChamada(registros=a.registros), ctx.user
    )


def _corrigir_frequencia(ctx: ToolContext, a: s.CorrigirFrequenciaInput) -> Any:
    return frequencia_service.corrigir_registro(
        ctx.db,
        a.turma_id,
        a.aluno_id,
        a.data or clock.today(),
        CorrigirRegistro(status=a.status, observacao=a.observacao),
        ctx.user,
    )


def _criar_cobranca(ctx: ToolContext, a: s.CriarCobrancaInput) -> Any:
    return financeiro_service.criar_cobranca_avulsa(ctx.db, a)


def _gerar_mensalidades(ctx: ToolContext, a: s.GerarMensalidadesInput) -> Any:
    return financeiro_service.gerar_mensalidades(ctx.db, a.competencia)


def _marcar_cobranca_paga(ctx: ToolContext, a: s.CobrancaIdInput) -> Any:
    return financeiro_service.marcar_cobranca_paga(ctx.db, a.cobranca_id, ctx.user)


def _criar_bolsa(ctx: ToolContext, a: s.CriarBolsaInput) -> Any:
    return financeiro_service.create_bolsa(ctx.db, a)


def _atualizar_bolsa(ctx: ToolContext, a: s.AtualizarBolsaInput) -> Any:
    dados = BolsaUpdate(**a.model_dump(exclude_unset=True, exclude={"bolsa_id"}))
    return financeiro_service.update_bolsa(ctx.db, a.bolsa_id, dados)


def _criar_preco(ctx: ToolContext, a: s.CriarPrecoInput) -> Any:
    return financeiro_service.create_preco(ctx.db, a)


def _atualizar_preco(ctx: ToolContext, a: s.AtualizarPrecoInput) -> Any:
    dados = TabelaPrecoUpdate(**a.model_dump(exclude_unset=True, exclude={"preco_id"}))
    return financeiro_service.update_preco(ctx.db, a.preco_id, dados)


def _criar_evento(ctx: ToolContext, a: s.CriarEventoInput) -> Any:
    return calendario_service.create_evento(ctx.db, a, ctx.user)


def _atualizar_evento(ctx: ToolContext, a: s.AtualizarEventoInput) -> Any:
    dados = EventoCalendarioUpdate(**a.model_dump(exclude_unset=True, exclude={"evento_id"}))
    return calendario_service.update_evento(ctx.db, a.evento_id, dados, ctx.user)


def _excluir_evento(ctx: ToolContext, a: s.EventoIdInput) -> Any:
    return calendario_service.delete_evento(ctx.db, a.evento_id, ctx.user)


def _criar_aviso(ctx: ToolContext, a: s.CriarAvisoInput) -> Any:
    return comunicacao_service.create_aviso(ctx.db, a, ctx.user)


def _atualizar_aviso(ctx: ToolContext, a: s.AtualizarAvisoInput) -> Any:
    dados = AvisoUpdate(**a.model_dump(exclude_unset=True, exclude={"aviso_id"}))
    return comunicacao_service.update_aviso(ctx.db, a.aviso_id, dados, ctx.user)


def _excluir_aviso(ctx: ToolContext, a: s.AvisoIdInput) -> Any:
    return comunicacao_service.delete_aviso(ctx.db, a.aviso_id, ctx.user)


def _marcar_aviso_lido(ctx: ToolContext, a: s.AvisoIdInput) -> Any:
    return comunicacao_service.marcar_lido(ctx.db, a.aviso_id, ctx.user)


# =============================================================================================
# PREVIEWS (texto do cartão de confirmação, montado a partir do banco)
# =============================================================================================


def _pv_criar_aluno(ctx: ToolContext, a: AlunoCreate) -> str:
    responsaveis = [
        f"{_responsavel(ctx, v.responsavel_id)} — {v.parentesco.value}"
        f"{' (financeiro)' if v.responsavel_financeiro else ''}"
        for v in a.responsaveis
    ]
    return _bloco(
        "Cadastrar novo aluno",
        ("Nome", a.nome),
        ("Nascimento", a.data_nascimento),
        ("Responsáveis", "; ".join(responsaveis)),
    )


def _pv_atualizar_aluno(ctx: ToolContext, a: s.AtualizarAlunoInput) -> str:
    return _bloco(
        f"Alterar dados do aluno {_aluno(ctx, a.aluno_id)}",
        *_mudancas(a, {"aluno_id"}),
    )


def _pv_excluir_aluno(ctx: ToolContext, a: s.AlunoIdInput) -> str:
    return (
        f"Excluir o cadastro do aluno {_aluno(ctx, a.aluno_id)}.\n"
        "O aluno deixa de aparecer nas listagens do sistema."
    )


def _pv_vincular(ctx: ToolContext, a: s.VincularResponsavelInput) -> str:
    return _bloco(
        "Vincular responsável ao aluno",
        ("Aluno", _aluno(ctx, a.aluno_id)),
        ("Responsável", _responsavel(ctx, a.responsavel_id)),
        ("Parentesco", a.parentesco),
        ("Responsável financeiro", a.responsavel_financeiro),
        ("Pode buscar o aluno", a.pode_buscar),
    )


def _pv_atualizar_vinculo(ctx: ToolContext, a: s.AtualizarVinculoInput) -> str:
    return _bloco(
        "Alterar vínculo entre aluno e responsável",
        ("Aluno", _aluno(ctx, a.aluno_id)),
        ("Responsável", _responsavel(ctx, a.responsavel_id)),
        *_mudancas(a, {"aluno_id", "responsavel_id"}),
    )


def _pv_remover_vinculo(ctx: ToolContext, a: s.RemoverVinculoInput) -> str:
    return _bloco(
        "Remover o vínculo entre aluno e responsável",
        ("Aluno", _aluno(ctx, a.aluno_id)),
        ("Responsável", _responsavel(ctx, a.responsavel_id)),
    )


def _pv_criar_responsavel(_: ToolContext, a: s.CriarResponsavelInput) -> str:
    return _bloco(
        "Cadastrar novo responsável",
        ("Nome", a.nome),
        ("CPF", a.cpf),
        ("E-mail", a.email),
        ("Telefone", a.telefone),
    )


def _pv_atualizar_responsavel(ctx: ToolContext, a: s.AtualizarResponsavelInput) -> str:
    return _bloco(
        f"Alterar dados do responsável {_responsavel(ctx, a.responsavel_id)}",
        *_mudancas(a, {"responsavel_id"}),
    )


def _pv_criar_turma(_: ToolContext, a: TurmaCreate) -> str:
    return _bloco(
        "Criar nova turma",
        ("Série", a.serie),
        ("Ano letivo", a.ano_letivo),
        ("Turno", a.turno),
        ("Capacidade", a.capacidade),
    )


def _pv_atualizar_turma(ctx: ToolContext, a: s.AtualizarTurmaInput) -> str:
    return _bloco(f"Alterar a turma {_turma(ctx, a.turma_id)}", *_mudancas(a, {"turma_id"}))


def _pv_adicionar_professor(ctx: ToolContext, a: s.ProfessorTurmaInput) -> str:
    return _bloco(
        "Adicionar professor à turma",
        ("Turma", _turma(ctx, a.turma_id)),
        ("Professor", _professor(ctx, a.professor_id)),
    )


def _pv_remover_professor(ctx: ToolContext, a: s.ProfessorTurmaInput) -> str:
    return _bloco(
        "Remover professor da turma",
        ("Turma", _turma(ctx, a.turma_id)),
        ("Professor", _professor(ctx, a.professor_id)),
    )


def _pv_criar_pre_matricula(ctx: ToolContext, a: s.CriarPreMatriculaInput) -> str:
    if a.aluno_id is not None:
        aluno = _aluno(ctx, a.aluno_id)
        tipo = "Rematrícula (aluno já cadastrado)"
    else:
        aluno = a.aluno.nome if a.aluno else "—"
        tipo = "Matrícula nova (ou rematrícula, se o CPF já existir)"
    return _bloco(
        "Registrar pré-matrícula",
        ("Aluno", aluno),
        ("Tipo", tipo),
        ("Série", a.serie),
        ("Ano letivo", a.ano_letivo),
        ("Turno", a.turno),
    )


def _pv_iniciar_analise(ctx: ToolContext, a: s.MatriculaIdInput) -> str:
    return f"Iniciar a análise da {_matricula(ctx, a.matricula_id)}."


def _pv_aprovar(ctx: ToolContext, a: s.AprovarMatriculaInput) -> str:
    turma = turmas_service.get_turma(ctx.db, a.turma_id, ctx.user)
    return _bloco(
        "Aprovar matrícula",
        ("Matrícula", _matricula(ctx, a.matricula_id)),
        ("Turma", f"{turma.nome} (id {turma.id})"),
        ("Vagas disponíveis na turma", turma.vagas_disponiveis),
    )


def _pv_rejeitar(ctx: ToolContext, a: s.MotivoMatriculaInput) -> str:
    return _bloco(
        "Rejeitar matrícula (em matrícula nova, o cadastro do aluno é cancelado)",
        ("Matrícula", _matricula(ctx, a.matricula_id)),
        ("Motivo", a.motivo),
    )


def _pv_cancelar(ctx: ToolContext, a: s.MotivoMatriculaInput) -> str:
    return _bloco(
        "Cancelar matrícula",
        ("Matrícula", _matricula(ctx, a.matricula_id)),
        ("Motivo", a.motivo),
    )


def _pv_documento(ctx: ToolContext, a: s.DocumentoMatriculaInput) -> str:
    acao = "Marcar como ENTREGUE" if a.entregue else "Marcar como PENDENTE"
    return _bloco(
        f"{acao} o documento da matrícula",
        ("Matrícula", _matricula(ctx, a.matricula_id)),
        ("Documento", DOCUMENTO_LABELS[a.tipo]),
    )


def _pv_lancar_nota(ctx: ToolContext, a: s.LancarNotaInput) -> str:
    aluno = _aluno(ctx, a.aluno_id)
    turma = _turma(ctx, a.turma_id)
    atual = notas_service.find_nota(ctx.db, a.aluno_id, a.turma_id, a.disciplina, a.periodo)
    pares: list[tuple[str, Any]] = [
        ("Aluno", aluno),
        ("Turma", turma),
        ("Disciplina", a.disciplina),
        ("Período", PERIODO_LABELS[a.periodo]),
    ]
    if atual is not None:
        pares.append(("Nota", f"{atual.valor:g} → {a.valor:g} (alteração)"))
        titulo = "Alterar nota"
    else:
        pares.append(("Nota", f"{a.valor:g}"))
        titulo = "Lançar nota"
    if a.observacao:
        pares.append(("Observação", a.observacao))
    return _bloco(titulo, *pares)


def _pv_lancar_chamada(ctx: ToolContext, a: s.LancarChamadaInput) -> str:
    data = a.data or clock.today()
    chamada = frequencia_service.get_chamada_do_dia(ctx.db, a.turma_id, data, ctx.user)
    nomes = {c.aluno_id: c.aluno_nome for c in chamada}
    desconhecidos = [r.aluno_id for r in a.registros if r.aluno_id not in nomes]
    if desconhecidos:
        raise NotFoundError(f"Aluno(s) {desconhecidos} não estão matriculados nesta turma.")
    linhas = [f"{nomes[r.aluno_id]}: {r.status.value}" for r in a.registros]
    return f"Lançar chamada de {_fmt(data)} — {_turma(ctx, a.turma_id)}\n" + "\n".join(
        f"• {linha}" for linha in linhas
    )


def _pv_corrigir_frequencia(ctx: ToolContext, a: s.CorrigirFrequenciaInput) -> str:
    return _bloco(
        "Registrar/corrigir frequência",
        ("Aluno", _aluno(ctx, a.aluno_id)),
        ("Turma", _turma(ctx, a.turma_id)),
        ("Data", a.data or clock.today()),
        ("Status", a.status),
        ("Observação", a.observacao),
    )


def _pv_criar_cobranca(ctx: ToolContext, a: s.CriarCobrancaInput) -> str:
    return _bloco(
        "Criar cobrança avulsa",
        ("Aluno", _aluno(ctx, a.aluno_id)),
        ("Tipo", a.tipo),
        ("Competência", a.competencia),
        ("Valor", a.valor_original),
        ("Vencimento", a.vencimento),
    )


def _pv_gerar_mensalidades(_: ToolContext, a: s.GerarMensalidadesInput) -> str:
    return (
        f"Gerar as mensalidades da competência {a.competencia} para TODOS os alunos ativos.\n"
        "Cobranças já existentes dessa competência não são duplicadas."
    )


def _pv_marcar_paga(ctx: ToolContext, a: s.CobrancaIdInput) -> str:
    c = financeiro_service.get_cobranca(ctx.db, a.cobranca_id)
    return _bloco(
        "Marcar cobrança como PAGA",
        ("Cobrança", f"#{c.id}"),
        ("Aluno", _aluno(ctx, c.aluno_id)),
        ("Tipo", c.tipo),
        ("Competência", c.competencia),
        ("Valor", c.valor_final),
        ("Vencimento", c.vencimento),
        ("Status atual", c.status),
    )


def _pv_criar_bolsa(ctx: ToolContext, a: s.CriarBolsaInput) -> str:
    return _bloco(
        "Conceder bolsa",
        ("Aluno", _aluno(ctx, a.aluno_id)),
        ("Desconto", f"{a.percentual_desconto}%"),
        ("Motivo", a.motivo),
        ("Início", a.vigencia_inicio),
        ("Fim", a.vigencia_fim),
    )


def _pv_atualizar_bolsa(ctx: ToolContext, a: s.AtualizarBolsaInput) -> str:
    bolsa = next(
        (b for b in financeiro_service.list_bolsas(ctx.db, aluno_id=None) if b.id == a.bolsa_id),
        None,
    )
    if bolsa is None:
        raise NotFoundError("Bolsa não encontrada.")
    return _bloco(
        f"Alterar a bolsa #{bolsa.id} de {_aluno(ctx, bolsa.aluno_id)}",
        *_mudancas(a, {"bolsa_id"}),
    )


def _pv_criar_preco(_: ToolContext, a: s.CriarPrecoInput) -> str:
    return _bloco(
        "Cadastrar preço",
        ("Série", a.serie),
        ("Ano letivo", a.ano_letivo),
        ("Matrícula", a.valor_matricula),
        ("Mensalidade", a.valor_mensalidade),
    )


def _pv_atualizar_preco(ctx: ToolContext, a: s.AtualizarPrecoInput) -> str:
    preco = next((p for p in financeiro_service.list_precos(ctx.db) if p.id == a.preco_id), None)
    if preco is None:
        raise NotFoundError("Preço não encontrado.")
    return _bloco(
        f"Alterar preço #{preco.id} ({preco.serie}, {preco.ano_letivo})",
        *_mudancas(a, {"preco_id"}),
    )


def _pv_criar_evento(ctx: ToolContext, a: s.CriarEventoInput) -> str:
    return _bloco(
        "Criar evento no calendário",
        ("Título", a.titulo),
        ("Tipo", a.tipo),
        ("Início", a.data_inicio),
        ("Fim", a.data_fim),
        ("Turma", _turma(ctx, a.turma_id) if a.turma_id else "Geral (toda a escola)"),
        ("Descrição", a.descricao),
    )


def _pv_atualizar_evento(ctx: ToolContext, a: s.AtualizarEventoInput) -> str:
    evento = calendario_service.get_evento(ctx.db, a.evento_id)
    return _bloco(
        f"Alterar evento «{evento.titulo}» ({_fmt(evento.data_inicio)})",
        *_mudancas(a, {"evento_id"}),
    )


def _pv_excluir_evento(ctx: ToolContext, a: s.EventoIdInput) -> str:
    evento = calendario_service.get_evento(ctx.db, a.evento_id)
    return f"Excluir o evento «{evento.titulo}» ({_fmt(evento.data_inicio)})."


def _pv_criar_aviso(ctx: ToolContext, a: s.CriarAvisoInput) -> str:
    corpo = a.corpo if len(a.corpo) <= 300 else a.corpo[:297] + "..."
    return _bloco(
        "Publicar aviso",
        ("Título", a.titulo),
        ("Público", a.publico_alvo),
        ("Turma", _turma(ctx, a.turma_id) if a.turma_id else None),
        ("Fixado", a.fixado),
        ("Texto", corpo),
    )


def _pv_atualizar_aviso(ctx: ToolContext, a: s.AtualizarAvisoInput) -> str:
    aviso = comunicacao_service.get_aviso(ctx.db, a.aviso_id)
    return _bloco(f"Alterar o aviso «{aviso.titulo}»", *_mudancas(a, {"aviso_id"}))


def _pv_excluir_aviso(ctx: ToolContext, a: s.AvisoIdInput) -> str:
    aviso = comunicacao_service.get_aviso(ctx.db, a.aviso_id)
    return f"Excluir o aviso «{aviso.titulo}»."


def _pv_marcar_aviso_lido(ctx: ToolContext, a: s.AvisoIdInput) -> str:
    aviso = comunicacao_service.get_aviso(ctx.db, a.aviso_id)
    return f"Marcar o aviso «{aviso.titulo}» como lido."


# =============================================================================================
# CATÁLOGO
# =============================================================================================


def _leitura(
    name: str,
    titulo: str,
    description: str,
    input_model: type[BaseModel],
    roles: tuple[Role, ...],
    handler: Handler,
) -> Tool:
    return Tool(name, titulo, description, input_model, roles, handler)


def _escrita(
    name: str,
    titulo: str,
    description: str,
    input_model: type[BaseModel],
    roles: tuple[Role, ...],
    handler: Handler,
    preview: Preview,
    *,
    destrutiva: bool = False,
) -> Tool:
    return Tool(
        name, titulo, description, input_model, roles, handler,
        mutates=True, destrutiva=destrutiva, preview=preview,
    )  # fmt: skip


_CATALOGO: list[Tool] = [
    # --- Ajuda e contexto -----------------------------------------------------------------
    _leitura(
        "consultar_ajuda",
        "Consultar ajuda",
        "Busca na base de conhecimento do sistema (regras, fluxos, perfis). Use para dúvidas "
        "como 'como funciona a matrícula?' ou 'o que é inadimplência?'.",
        s.AjudaInput,
        perm.TODOS,
        _consultar_ajuda,
    ),
    _leitura(
        "quem_sou_eu",
        "Meu perfil",
        "Mostra o usuário logado, o perfil e (para responsável/aluno/professor) os ids "
        "vinculados a ele. Use para descobrir o id do aluno ou dos filhos do usuário.",
        s.SemArgumentos,
        perm.TODOS,
        _quem_sou_eu,
    ),
    # --- Pessoas: leitura -----------------------------------------------------------------
    _leitura(
        "buscar_alunos",
        "Buscar alunos",
        "Lista alunos por parte do nome (ou CPF completo). Use para descobrir o aluno_id antes "
        "de qualquer outra operação sobre um aluno.",
        s.BuscaInput,
        perm.EQUIPE,
        _buscar_alunos,
    ),
    _leitura(
        "obter_aluno",
        "Dados do aluno",
        "Dados cadastrais de um aluno e seus responsáveis (vínculos).",
        s.AlunoIdInput,
        perm.EQUIPE_E_FAMILIA,
        _obter_aluno,
    ),
    _leitura(
        "listar_meus_alunos",
        "Meus alunos",
        "Lista os alunos vinculados ao responsável logado.",
        s.SemArgumentos,
        perm.SOMENTE_RESPONSAVEL,
        _listar_meus_alunos,
    ),
    _leitura(
        "obter_meu_cadastro",
        "Meu cadastro",
        "Dados do próprio aluno logado.",
        s.SemArgumentos,
        perm.SOMENTE_ALUNO,
        _obter_meu_cadastro,
    ),
    _leitura(
        "buscar_responsaveis",
        "Buscar responsáveis",
        "Lista responsáveis por parte do nome (ou CPF completo).",
        s.BuscaInput,
        perm.EQUIPE,
        _buscar_responsaveis,
    ),
    _leitura(
        "obter_responsavel",
        "Dados do responsável",
        "Dados de contato de um responsável.",
        s.ResponsavelIdInput,
        perm.EQUIPE,
        _obter_responsavel,
    ),
    _leitura(
        "buscar_professores",
        "Buscar professores",
        "Lista professores por parte do nome (ou CPF completo).",
        s.BuscaInput,
        perm.SECRETARIA_ADMIN,
        _buscar_professores,
    ),
    # --- Turmas ---------------------------------------------------------------------------
    _leitura(
        "listar_turmas",
        "Listar turmas",
        "Lista turmas com série, turno, capacidade, vagas e professores. Filtros opcionais.",
        s.ListarTurmasInput,
        perm.EQUIPE,
        _listar_turmas,
    ),
    _leitura(
        "obter_turma",
        "Dados da turma",
        "Detalhes de uma turma (vagas, professores).",
        s.TurmaIdInput,
        perm.EQUIPE_E_PROFESSOR,
        _obter_turma,
    ),
    _leitura(
        "listar_minhas_turmas",
        "Minhas turmas",
        "Turmas em que o professor logado leciona.",
        s.SemArgumentos,
        perm.SOMENTE_PROFESSOR,
        _listar_minhas_turmas,
    ),
    # --- Matrículas -----------------------------------------------------------------------
    _leitura(
        "listar_matriculas",
        "Listar matrículas",
        "Lista matrículas com filtros de status, ano letivo e série. Responsável vê só as dos "
        "próprios filhos.",
        s.ListarMatriculasInput,
        perm.MATRICULA_LEITURA,
        _listar_matriculas,
    ),
    _leitura(
        "obter_matricula",
        "Dados da matrícula",
        "Detalhes de uma matrícula (status, turma, motivo de rejeição/cancelamento).",
        s.MatriculaIdInput,
        perm.MATRICULA_LEITURA,
        _obter_matricula,
    ),
    # --- Notas ----------------------------------------------------------------------------
    _leitura(
        "listar_disciplinas",
        "Disciplinas",
        "Lista as disciplinas válidas para lançamento de notas.",
        s.SemArgumentos,
        perm.TODOS,
        _listar_disciplinas,
    ),
    _leitura(
        "obter_boletim",
        "Boletim do aluno",
        "Boletim: notas por disciplina e bimestre, média e situação (aprovado/recuperação/"
        "reprovado).",
        s.AlunoIdInput,
        perm.ACADEMICO_E_FAMILIA,
        _obter_boletim,
    ),
    _leitura(
        "ver_notas_da_turma",
        "Notas da turma",
        "Notas de todos os alunos de uma turma em um bimestre.",
        s.GradeNotasInput,
        perm.ACADEMICO,
        _ver_grade_notas,
    ),
    # --- Frequência -----------------------------------------------------------------------
    _leitura(
        "ver_chamada_do_dia",
        "Chamada do dia",
        "Lista de alunos da turma com o status de presença já lançado na data (padrão: hoje).",
        s.ChamadaDiaInput,
        perm.ACADEMICO,
        _ver_chamada,
    ),
    _leitura(
        "ver_frequencia_do_aluno",
        "Frequência do aluno",
        "Histórico de presenças e percentual de presença do aluno em um período (padrão: "
        "últimos 30 dias).",
        s.HistoricoFrequenciaInput,
        perm.ACADEMICO_E_FAMILIA,
        _ver_frequencia_aluno,
    ),
    # --- Financeiro -----------------------------------------------------------------------
    _leitura(
        "listar_cobrancas",
        "Listar cobranças",
        "Lista cobranças (mensalidades, matrícula, taxas) com filtros de aluno e status. "
        "Responsável/aluno veem só as próprias.",
        s.ListarCobrancasInput,
        perm.FINANCEIRO_LEITURA,
        _listar_cobrancas,
    ),
    _leitura(
        "verificar_inadimplencia",
        "Verificar inadimplência",
        "Informa se o aluno está inadimplente (cobrança vencida há mais de 5 dias).",
        s.AlunoIdInput,
        perm.FINANCEIRO_ADMIN,
        _verificar_inadimplencia,
    ),
    _leitura(
        "listar_bolsas",
        "Listar bolsas",
        "Lista bolsas de desconto (todas ou de um aluno).",
        s.ListarBolsasInput,
        perm.FINANCEIRO_ADMIN,
        _listar_bolsas,
    ),
    _leitura(
        "listar_precos",
        "Tabela de preços",
        "Lista a tabela de preços (matrícula e mensalidade por série e ano letivo).",
        s.SemArgumentos,
        perm.FINANCEIRO_ADMIN,
        _listar_precos,
    ),
    # --- Calendário e comunicação ---------------------------------------------------------
    _leitura(
        "listar_eventos",
        "Eventos do calendário",
        "Lista eventos do calendário escolar em um período (padrão: próximos 60 dias).",
        s.ListarEventosInput,
        perm.TODOS,
        _listar_eventos,
    ),
    _leitura(
        "listar_avisos",
        "Avisos",
        "Lista os avisos visíveis ao usuário, do mais recente ao mais antigo.",
        s.LimiteInput,
        perm.TODOS,
        _listar_avisos,
    ),
    _leitura(
        "contar_avisos_nao_lidos",
        "Avisos não lidos",
        "Quantidade de avisos não lidos do usuário.",
        s.SemArgumentos,
        perm.TODOS,
        _contar_avisos_nao_lidos,
    ),
    # =========================== ESCRITA (exigem confirmação) ===========================
    # --- Pessoas --------------------------------------------------------------------------
    _escrita(
        "criar_aluno",
        "Cadastrar aluno",
        "Cadastra um aluno novo. Exige 1 a 4 responsáveis JÁ cadastrados (responsavel_id), com "
        "exatamente 1 financeiro.",
        AlunoCreate,
        perm.SECRETARIA_ADMIN,
        _criar_aluno,
        _pv_criar_aluno,
    ),
    _escrita(
        "atualizar_aluno",
        "Alterar aluno",
        "Altera nome, data de nascimento ou CPF de um aluno. Envie só o que muda.",
        s.AtualizarAlunoInput,
        perm.SECRETARIA_ADMIN,
        _atualizar_aluno,
        _pv_atualizar_aluno,
    ),
    _escrita(
        "excluir_aluno",
        "Excluir aluno",
        "Exclui o cadastro de um aluno (exclusão lógica). Use apenas quando o usuário pedir "
        "explicitamente.",
        s.AlunoIdInput,
        perm.SOMENTE_ADMIN,
        _excluir_aluno,
        _pv_excluir_aluno,
        destrutiva=True,
    ),
    _escrita(
        "vincular_responsavel",
        "Vincular responsável",
        "Vincula um responsável já cadastrado a um aluno.",
        s.VincularResponsavelInput,
        perm.SECRETARIA_ADMIN,
        _vincular_responsavel,
        _pv_vincular,
    ),
    _escrita(
        "atualizar_vinculo",
        "Alterar vínculo",
        "Altera parentesco, permissão de buscar ou torna o responsável o financeiro do aluno.",
        s.AtualizarVinculoInput,
        perm.SECRETARIA_ADMIN,
        _atualizar_vinculo,
        _pv_atualizar_vinculo,
    ),
    _escrita(
        "remover_vinculo",
        "Remover vínculo",
        "Remove o vínculo de um responsável com um aluno (não pode ser o último nem o financeiro).",
        s.RemoverVinculoInput,
        perm.SECRETARIA_ADMIN,
        _remover_vinculo,
        _pv_remover_vinculo,
        destrutiva=True,
    ),
    _escrita(
        "criar_responsavel",
        "Cadastrar responsável",
        "Cadastra um responsável (sem criar login).",
        s.CriarResponsavelInput,
        perm.SECRETARIA_ADMIN,
        _criar_responsavel,
        _pv_criar_responsavel,
    ),
    _escrita(
        "atualizar_responsavel",
        "Alterar responsável",
        "Altera nome, e-mail ou telefone de um responsável.",
        s.AtualizarResponsavelInput,
        perm.SECRETARIA_ADMIN,
        _atualizar_responsavel,
        _pv_atualizar_responsavel,
    ),
    # --- Turmas ---------------------------------------------------------------------------
    _escrita(
        "criar_turma",
        "Criar turma",
        "Cria uma turma (série + ano letivo + turno). Capacidade máxima 30.",
        TurmaCreate,
        perm.SECRETARIA_ADMIN,
        _criar_turma,
        _pv_criar_turma,
    ),
    _escrita(
        "atualizar_turma",
        "Alterar turma",
        "Altera a capacidade ou ativa/desativa uma turma.",
        s.AtualizarTurmaInput,
        perm.SECRETARIA_ADMIN,
        _atualizar_turma,
        _pv_atualizar_turma,
    ),
    _escrita(
        "adicionar_professor_na_turma",
        "Adicionar professor à turma",
        "Adiciona um professor a uma turma.",
        s.ProfessorTurmaInput,
        perm.SECRETARIA_ADMIN,
        _adicionar_professor,
        _pv_adicionar_professor,
    ),
    _escrita(
        "remover_professor_da_turma",
        "Remover professor da turma",
        "Remove um professor de uma turma.",
        s.ProfessorTurmaInput,
        perm.SECRETARIA_ADMIN,
        _remover_professor,
        _pv_remover_professor,
        destrutiva=True,
    ),
    # --- Matrículas -----------------------------------------------------------------------
    _escrita(
        "criar_pre_matricula",
        "Registrar pré-matrícula",
        "Registra uma pré-matrícula. Informe aluno_id (rematrícula) ou os dados do aluno "
        "(matrícula nova), mais série, turno e ano letivo.",
        s.CriarPreMatriculaInput,
        perm.MATRICULA_CRIAR_CANCELAR,
        _criar_pre_matricula,
        _pv_criar_pre_matricula,
    ),
    _escrita(
        "iniciar_analise_matricula",
        "Iniciar análise da matrícula",
        "Move a matrícula de PRE_MATRICULA para EM_ANALISE.",
        s.MatriculaIdInput,
        perm.SECRETARIA_ADMIN,
        _iniciar_analise,
        _pv_iniciar_analise,
    ),
    _escrita(
        "aprovar_matricula",
        "Aprovar matrícula",
        "Aprova uma matrícula EM_ANALISE em uma turma da mesma série e ano letivo. Exige "
        "documentos entregues e vaga na turma.",
        s.AprovarMatriculaInput,
        perm.SECRETARIA_ADMIN,
        _aprovar_matricula,
        _pv_aprovar,
    ),
    _escrita(
        "rejeitar_matricula",
        "Rejeitar matrícula",
        "Rejeita uma matrícula, com motivo. Em matrícula nova, cancela o cadastro do aluno.",
        s.MotivoMatriculaInput,
        perm.SECRETARIA_ADMIN,
        _rejeitar_matricula,
        _pv_rejeitar,
        destrutiva=True,
    ),
    _escrita(
        "cancelar_matricula",
        "Cancelar matrícula",
        "Cancela uma matrícula, com motivo. Responsável só cancela pré-matrícula dos filhos "
        "antes da análise.",
        s.MotivoMatriculaInput,
        perm.MATRICULA_CRIAR_CANCELAR,
        _cancelar_matricula,
        _pv_cancelar,
        destrutiva=True,
    ),
    _escrita(
        "marcar_documento_matricula",
        "Conferir documento",
        "Marca um documento da matrícula como entregue (ou pendente).",
        s.DocumentoMatriculaInput,
        perm.SECRETARIA_ADMIN,
        _marcar_documento,
        _pv_documento,
    ),
    # --- Notas e frequência ---------------------------------------------------------------
    _escrita(
        "lancar_nota",
        "Lançar/alterar nota",
        "Lança a nota (0 a 10) de um aluno em uma disciplina e bimestre; se já existir nota "
        "nessa disciplina/bimestre, ela é ALTERADA. Professor só lança nas próprias turmas.",
        s.LancarNotaInput,
        perm.ACADEMICO,
        _lancar_nota,
        _pv_lancar_nota,
    ),
    _escrita(
        "lancar_chamada",
        "Lançar chamada",
        "Dá presença/falta para vários alunos de uma turma em uma data (padrão: hoje). Status: "
        "PRESENTE, FALTA, FALTA_JUSTIFICADA.",
        s.LancarChamadaInput,
        perm.ACADEMICO,
        _lancar_chamada,
        _pv_lancar_chamada,
    ),
    _escrita(
        "corrigir_frequencia",
        "Registrar/corrigir frequência",
        "Registra ou corrige a presença/falta de UM aluno em uma data (padrão: hoje).",
        s.CorrigirFrequenciaInput,
        perm.ACADEMICO,
        _corrigir_frequencia,
        _pv_corrigir_frequencia,
    ),
    # --- Financeiro -----------------------------------------------------------------------
    _escrita(
        "criar_cobranca_avulsa",
        "Criar cobrança avulsa",
        "Cria uma cobrança avulsa (MATRICULA ou TAXA_EXTRA) para um aluno.",
        s.CriarCobrancaInput,
        perm.FINANCEIRO_ADMIN,
        _criar_cobranca,
        _pv_criar_cobranca,
    ),
    _escrita(
        "gerar_mensalidades",
        "Gerar mensalidades",
        "Gera as mensalidades de um mês (AAAA-MM) para todos os alunos ativos. Ação em lote.",
        s.GerarMensalidadesInput,
        perm.FINANCEIRO_ADMIN,
        _gerar_mensalidades,
        _pv_gerar_mensalidades,
        destrutiva=True,
    ),
    _escrita(
        "marcar_cobranca_paga",
        "Dar baixa em cobrança",
        "Marca uma cobrança como paga.",
        s.CobrancaIdInput,
        perm.FINANCEIRO_ADMIN,
        _marcar_cobranca_paga,
        _pv_marcar_paga,
    ),
    _escrita(
        "criar_bolsa",
        "Conceder bolsa",
        "Concede uma bolsa de desconto (percentual) a um aluno.",
        s.CriarBolsaInput,
        perm.FINANCEIRO_ADMIN,
        _criar_bolsa,
        _pv_criar_bolsa,
    ),
    _escrita(
        "atualizar_bolsa",
        "Alterar bolsa",
        "Altera percentual, motivo ou vigência de uma bolsa.",
        s.AtualizarBolsaInput,
        perm.FINANCEIRO_ADMIN,
        _atualizar_bolsa,
        _pv_atualizar_bolsa,
    ),
    _escrita(
        "criar_preco",
        "Cadastrar preço",
        "Cadastra preço de matrícula e mensalidade para uma série e ano letivo.",
        s.CriarPrecoInput,
        perm.FINANCEIRO_ADMIN,
        _criar_preco,
        _pv_criar_preco,
    ),
    _escrita(
        "atualizar_preco",
        "Alterar preço",
        "Altera os valores de uma entrada da tabela de preços.",
        s.AtualizarPrecoInput,
        perm.FINANCEIRO_ADMIN,
        _atualizar_preco,
        _pv_atualizar_preco,
    ),
    # --- Calendário -----------------------------------------------------------------------
    _escrita(
        "criar_evento",
        "Criar evento",
        "Cria um evento no calendário (geral ou de uma turma). Professor só para as próprias "
        "turmas.",
        s.CriarEventoInput,
        perm.ACADEMICO,
        _criar_evento,
        _pv_criar_evento,
    ),
    _escrita(
        "atualizar_evento",
        "Alterar evento",
        "Altera um evento do calendário.",
        s.AtualizarEventoInput,
        perm.ACADEMICO,
        _atualizar_evento,
        _pv_atualizar_evento,
    ),
    _escrita(
        "excluir_evento",
        "Excluir evento",
        "Exclui um evento do calendário.",
        s.EventoIdInput,
        perm.ACADEMICO,
        _excluir_evento,
        _pv_excluir_evento,
        destrutiva=True,
    ),
    # --- Comunicação ----------------------------------------------------------------------
    _escrita(
        "criar_aviso",
        "Publicar aviso",
        "Publica um aviso para TODOS, uma TURMA (informe turma_id), RESPONSAVEIS ou "
        "PROFESSORES. Professor só para turmas em que leciona.",
        s.CriarAvisoInput,
        perm.ACADEMICO,
        _criar_aviso,
        _pv_criar_aviso,
    ),
    _escrita(
        "atualizar_aviso",
        "Alterar aviso",
        "Altera um aviso já publicado.",
        s.AtualizarAvisoInput,
        perm.ACADEMICO,
        _atualizar_aviso,
        _pv_atualizar_aviso,
    ),
    _escrita(
        "excluir_aviso",
        "Excluir aviso",
        "Exclui um aviso.",
        s.AvisoIdInput,
        perm.ACADEMICO,
        _excluir_aviso,
        _pv_excluir_aviso,
        destrutiva=True,
    ),
    _escrita(
        "marcar_aviso_lido",
        "Marcar aviso como lido",
        "Marca um aviso como lido para o usuário logado.",
        s.AvisoIdInput,
        perm.TODOS,
        _marcar_aviso_lido,
        _pv_marcar_aviso_lido,
    ),
]

TOOLS: dict[str, Tool] = {t.name: t for t in _CATALOGO}
assert len(TOOLS) == len(_CATALOGO), "Nome de ferramenta duplicado"  # noqa: S101
assert all(t.preview is not None for t in _CATALOGO if t.mutates)  # noqa: S101


def get_tool(name: str) -> Tool | None:
    return TOOLS.get(name)


def tools_for_role(role: Role) -> list[Tool]:
    return [t for t in _CATALOGO if role in t.roles]


def specs_for_role(role: Role) -> list[dict[str, Any]]:
    return [t.spec() for t in tools_for_role(role)]
