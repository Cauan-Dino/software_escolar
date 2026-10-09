"""Testes ponta a ponta (HTTP) do assistente, com LLM falso."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import AuditLog
from app.core.roles import Role
from app.modules.assistente.models import AcaoPendente, StatusAcao
from app.modules.auth.models import User
from app.modules.notas.models import Nota
from app.shared import clock
from tests.factories import (
    headers_of,
    make_aluno,
    make_professor,
    make_responsavel,
    make_user,
    responsavel_headers,
)
from tests.modules.assistente.fakes import chamar, chamar_json_bruto, chamar_varias, texto

BASE = "/api/v1/assistente"


def _nova_conversa(client, headers) -> int:
    resp = client.post(f"{BASE}/conversas", headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _enviar(client, headers, conversa_id: int, mensagem: str = "oi"):
    return client.post(
        f"{BASE}/conversas/{conversa_id}/mensagens", json={"texto": mensagem}, headers=headers
    )


def _notas(db: Session) -> list[Nota]:
    return list(db.scalars(select(Nota)))


# --- Conversas ------------------------------------------------------------------------------


def test_requires_authentication(client):
    assert client.post(f"{BASE}/conversas").status_code == 401
    assert client.get(f"{BASE}/conversas").status_code == 401


def test_conversa_crud_and_isolation_between_users(client, db, admin):
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)

    assert [c["id"] for c in client.get(f"{BASE}/conversas", headers=headers).json()] == [
        conversa_id
    ]
    detalhe = client.get(f"{BASE}/conversas/{conversa_id}", headers=headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["mensagens"] == []

    outro = headers_of(make_user(db, Role.SECRETARIA))
    assert client.get(f"{BASE}/conversas/{conversa_id}", headers=outro).status_code == 404
    assert client.delete(f"{BASE}/conversas/{conversa_id}", headers=outro).status_code == 404

    assert client.delete(f"{BASE}/conversas/{conversa_id}", headers=headers).status_code == 204
    assert client.get(f"{BASE}/conversas/{conversa_id}", headers=headers).status_code == 404


def test_plain_text_answer_is_persisted_and_titles_the_conversa(client, admin, usar_llm):
    fake = usar_llm(texto("Olá! Como posso ajudar?"))
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)

    resp = _enviar(client, headers, conversa_id, "Oi, tudo bem?")
    assert resp.status_code == 200
    mensagens = resp.json()["mensagens"]
    assert [m["role"] for m in mensagens] == ["user", "assistant"]
    assert mensagens[1]["conteudo"] == "Olá! Como posso ajudar?"

    primeiro = fake.chamadas[0]["messages"]
    assert primeiro[0]["role"] == "system"
    assert "ADMIN" in primeiro[0]["content"]

    detalhe = client.get(f"{BASE}/conversas/{conversa_id}", headers=headers).json()
    assert detalhe["titulo"] == "Oi, tudo bem?"
    assert len(detalhe["mensagens"]) == 2


def test_history_is_sent_to_the_model_on_the_next_message(client, admin, usar_llm):
    fake = usar_llm(texto("primeira"), texto("segunda"))
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    _enviar(client, headers, conversa_id, "um")
    _enviar(client, headers, conversa_id, "dois")

    roles = [m["role"] for m in fake.chamadas[1]["messages"]]
    assert roles == ["system", "user", "assistant", "user"]


# --- Ferramentas de leitura -----------------------------------------------------------------


def test_read_tool_runs_and_result_goes_back_to_the_model(client, db, admin, aluno, usar_llm):
    fake = usar_llm(chamar("buscar_alunos", busca="Joana"), texto("Encontrei a Joana Souza."))
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)

    resp = _enviar(client, headers, conversa_id, "procure a Joana")
    assert resp.status_code == 200
    assert resp.json()["mensagens"][-1]["conteudo"] == "Encontrei a Joana Souza."

    retorno = fake.ultimas_mensagens_tool()
    assert len(retorno) == 1
    assert "Joana Souza" in retorno[0]["content"]
    assert "cpf" not in retorno[0]["content"].lower()


def test_unknown_tool_and_invalid_arguments_are_reported_to_the_model(client, admin, usar_llm):
    fake = usar_llm(
        chamar("ferramenta_que_nao_existe"),
        chamar_json_bruto("buscar_alunos", '{"limite": 9999}'),
        chamar_json_bruto("buscar_alunos", "isto nao e json"),
        texto("Desculpe, não consegui."),
    )
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id)
    assert resp.status_code == 200
    retornos = [m["content"] for m in fake.chamadas[-1]["messages"] if m["role"] == "tool"]
    assert len(retornos) == 3
    assert "FERRAMENTA_INDISPONIVEL" in retornos[0]
    assert "ARGUMENTOS_INVALIDOS" in retornos[1]
    assert "ARGUMENTOS_INVALIDOS" in retornos[2]


def test_loop_stops_after_max_steps(client, admin, usar_llm):
    usar_llm(*[chamar("listar_disciplinas") for _ in range(10)])
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id)
    assert resp.status_code == 200
    assert "reformul" in resp.json()["mensagens"][-1]["conteudo"]


def test_consultar_ajuda_returns_knowledge(client, admin, usar_llm):
    fake = usar_llm(chamar("consultar_ajuda", topico="fluxo da matrícula"), texto("ok"))
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    _enviar(client, headers, conversa_id, "como funciona a matrícula?")
    assert "EM_ANALISE" in fake.ultimas_mensagens_tool()[0]["content"]


# --- Permissões -----------------------------------------------------------------------------


def test_model_only_sees_tools_of_the_user_role(client, db, usar_llm):
    responsavel = make_responsavel(db)
    fake = usar_llm(texto("ok"))
    headers = responsavel_headers(db, responsavel)
    conversa_id = _nova_conversa(client, headers)
    _enviar(client, headers, conversa_id)
    nomes = fake.nomes_das_tools
    assert "listar_meus_alunos" in nomes
    assert "aprovar_matricula" not in nomes
    assert "lancar_nota" not in nomes
    assert "excluir_aluno" not in nomes


def test_forbidden_tool_call_is_refused_even_if_model_emits_it(client, db, aluno, turma, usar_llm):
    responsavel = make_responsavel(db)
    fake = usar_llm(
        chamar("excluir_aluno", aluno_id=aluno.id),
        chamar(
            "lancar_nota",
            turma_id=turma.id,
            aluno_id=aluno.id,
            disciplina="Português",
            periodo="BIMESTRE_1",
            valor=10,
        ),
        texto("Não posso fazer isso."),
    )
    headers = responsavel_headers(db, responsavel)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id, "apague o aluno")
    assert resp.status_code == 200
    assert not [m for m in resp.json()["mensagens"] if m["role"] == "acao"]
    assert "FERRAMENTA_INDISPONIVEL" in fake.ultimas_mensagens_tool()[0]["content"]
    assert db.scalar(select(AcaoPendente)) is None


def test_responsavel_cannot_read_unlinked_aluno(client, db, aluno, usar_llm):
    responsavel = make_responsavel(db)
    outro_aluno = make_aluno(db, responsaveis=[responsavel], nome="Filho Meu")
    fake = usar_llm(chamar("obter_aluno", aluno_id=aluno.id), texto("ok"))
    headers = responsavel_headers(db, responsavel)
    conversa_id = _nova_conversa(client, headers)
    _enviar(client, headers, conversa_id)
    retorno = fake.ultimas_mensagens_tool()[0]["content"]
    assert "Joana" not in retorno
    assert "erro" in retorno
    assert outro_aluno.id != aluno.id


# --- Confirmação por botão ---------------------------------------------------------------------


def _propor_nota(client, headers, usar_llm, aluno, turma, valor=8.5):
    usar_llm(
        chamar(
            "lancar_nota",
            turma_id=turma.id,
            aluno_id=aluno.id,
            disciplina="Matemática",
            periodo="BIMESTRE_2",
            valor=valor,
        ),
        texto("Aguardando a sua confirmação."),
    )
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id, "lance 8,5 em matemática pra Joana")
    assert resp.status_code == 200
    cartoes = [m for m in resp.json()["mensagens"] if m["role"] == "acao"]
    assert len(cartoes) == 1
    return conversa_id, cartoes[0]["acao"]


def test_write_tool_creates_pending_action_and_changes_nothing(
    client, db, admin, aluno, turma, usar_llm
):
    headers = headers_of(admin)
    _, acao = _propor_nota(client, headers, usar_llm, aluno, turma)

    assert acao["status"] == "PENDENTE"
    assert acao["ferramenta"] == "lancar_nota"
    assert "Joana Souza" in acao["resumo"]
    assert "Matemática" in acao["resumo"]
    assert "8.5" in acao["resumo"]
    assert _notas(db) == []  # NADA foi gravado antes do clique


def test_confirm_executes_once_and_audits(client, db, admin, aluno, turma, usar_llm):
    headers = headers_of(admin)
    conversa_id, acao = _propor_nota(client, headers, usar_llm, aluno, turma)

    resp = client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["acao"]["status"] == "CONFIRMADA"
    assert corpo["acao"]["resultado"]["valor"] == 8.5
    assert "✅" in corpo["mensagens"][0]["conteudo"]

    notas = _notas(db)
    assert len(notas) == 1
    assert (notas[0].aluno_id, float(notas[0].valor), notas[0].lancado_por_user_id) == (
        aluno.id,
        8.5,
        admin.id,
    )
    log = db.scalar(select(AuditLog).where(AuditLog.action == "assistente.lancar_nota"))
    assert log is not None and log.actor_user_id == admin.id

    # segundo clique não executa de novo
    again = client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers)
    assert again.status_code == 409
    assert again.json()["code"] == "ACAO_NAO_PENDENTE"
    assert len(_notas(db)) == 1

    detalhe = client.get(f"{BASE}/conversas/{conversa_id}", headers=headers).json()
    cartao = next(m for m in detalhe["mensagens"] if m["role"] == "acao")
    assert cartao["acao"]["status"] == "CONFIRMADA"


def test_editing_an_existing_nota_shows_old_and_new_value(
    client, db, admin, aluno, turma, usar_llm
):
    headers = headers_of(admin)
    _, primeira = _propor_nota(client, headers, usar_llm, aluno, turma, valor=5)
    client.post(f"{BASE}/acoes/{primeira['id']}/confirmar", headers=headers)

    _, segunda = _propor_nota(client, headers, usar_llm, aluno, turma, valor=9)
    assert "5 → 9" in segunda["resumo"]
    client.post(f"{BASE}/acoes/{segunda['id']}/confirmar", headers=headers)
    notas = _notas(db)
    assert len(notas) == 1 and float(notas[0].valor) == 9


def test_cancel_does_nothing_and_blocks_later_confirm(client, db, admin, aluno, turma, usar_llm):
    headers = headers_of(admin)
    _, acao = _propor_nota(client, headers, usar_llm, aluno, turma)

    resp = client.post(f"{BASE}/acoes/{acao['id']}/cancelar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["acao"]["status"] == "CANCELADA"
    assert _notas(db) == []

    assert client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers).status_code == 409
    assert _notas(db) == []


def test_other_user_cannot_confirm_or_cancel(client, db, admin, aluno, turma, usar_llm):
    headers = headers_of(admin)
    _, acao = _propor_nota(client, headers, usar_llm, aluno, turma)
    outro = headers_of(make_user(db, Role.ADMIN))

    assert client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=outro).status_code == 404
    assert client.post(f"{BASE}/acoes/{acao['id']}/cancelar", headers=outro).status_code == 404
    assert _notas(db) == []


def test_expired_action_cannot_be_confirmed(client, db, admin, aluno, turma, usar_llm):
    headers = headers_of(admin)
    _, acao = _propor_nota(client, headers, usar_llm, aluno, turma)
    registro = db.get(AcaoPendente, acao["id"])
    registro.expira_em = clock.now() - timedelta(minutes=1)
    db.flush()

    resp = client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers)
    assert resp.status_code == 409
    assert db.get(AcaoPendente, acao["id"]).status == StatusAcao.EXPIRADA
    assert _notas(db) == []


def test_professor_of_another_turma_cannot_propose_a_nota(
    client, db, aluno, turma, professor_da_turma, usar_llm
):
    """A proposta já é recusada: o professor não enxerga a turma de outro."""
    outro_prof = make_professor(db)
    headers = headers_of(db.get(User, outro_prof.user_id))
    usar_llm(
        chamar(
            "lancar_nota",
            turma_id=turma.id,
            aluno_id=aluno.id,
            disciplina="Artes",
            periodo="BIMESTRE_1",
            valor=7,
        ),
        texto("Não foi possível."),
    )
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id, "lance nota")
    assert resp.status_code == 200
    assert not [m for m in resp.json()["mensagens"] if m["role"] == "acao"]
    assert _notas(db) == []


def test_professor_of_the_turma_can_propose_and_confirm_a_nota(
    client, db, aluno, turma, professor_da_turma, usar_llm
):
    headers = headers_of(db.get(User, professor_da_turma.user_id))
    _, acao = _propor_nota(client, headers, usar_llm, aluno, turma)
    resp = client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers)
    assert resp.status_code == 200
    assert len(_notas(db)) == 1


def test_action_failing_at_confirm_is_recorded_as_failed(client, db, admin, aluno, turma, usar_llm):
    headers = headers_of(admin)
    # O estado muda entre a proposta e o clique (aluno inexistente): a confirmação revalida.
    _, acao = _propor_nota(client, headers, usar_llm, aluno, turma)
    registro = db.get(AcaoPendente, acao["id"])
    registro.argumentos = {**registro.argumentos, "aluno_id": 987654321}
    db.flush()

    resp = client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["acao"]["status"] == "FALHOU"
    assert "⚠️" in resp.json()["mensagens"][0]["conteudo"]
    assert _notas(db) == []

    assert db.get(AcaoPendente, acao["id"]).status == StatusAcao.FALHOU


def test_multiple_writes_in_one_turn_create_one_card_each(
    client, db, admin, aluno, turma, usar_llm
):
    usar_llm(
        chamar_varias(
            (
                "lancar_nota",
                {
                    "turma_id": turma.id,
                    "aluno_id": aluno.id,
                    "disciplina": "Artes",
                    "periodo": "BIMESTRE_1",
                    "valor": 7,
                },
            ),
            (
                "lancar_nota",
                {
                    "turma_id": turma.id,
                    "aluno_id": aluno.id,
                    "disciplina": "Inglês",
                    "periodo": "BIMESTRE_1",
                    "valor": 9,
                },
            ),
        ),
        texto("não deve ser consumida neste turno"),
    )
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id)
    cartoes = [m for m in resp.json()["mensagens"] if m["role"] == "acao"]
    assert len(cartoes) == 2
    assert _notas(db) == []


def test_preview_with_nonexistent_id_is_refused(client, db, admin, turma, usar_llm):
    fake = usar_llm(
        chamar(
            "lancar_nota",
            turma_id=turma.id,
            aluno_id=999999,
            disciplina="Artes",
            periodo="BIMESTRE_1",
            valor=7,
        ),
        texto("Aluno não encontrado."),
    )
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id)
    assert not [m for m in resp.json()["mensagens"] if m["role"] == "acao"]
    assert "NOT_FOUND" in fake.ultimas_mensagens_tool()[0]["content"]
    assert db.scalar(select(AcaoPendente)) is None


def test_chamada_flow_gives_presence_after_confirmation(
    client, db, admin, aluno, turma, matricula_ativa, usar_llm
):
    from app.modules.frequencia.models import Frequencia

    usar_llm(
        chamar(
            "lancar_chamada",
            turma_id=turma.id,
            registros=[{"aluno_id": aluno.id, "status": "PRESENTE"}],
        ),
        texto("ok"),
    )
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id, "marque presença da Joana")
    acao = next(m for m in resp.json()["mensagens"] if m["role"] == "acao")["acao"]
    assert "Joana Souza: PRESENTE" in acao["resumo"]
    assert db.scalar(select(Frequencia)) is None

    assert client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers).status_code == 200
    registro = db.scalar(select(Frequencia))
    assert registro is not None and registro.aluno_id == aluno.id


def test_excluir_aluno_is_admin_only_and_destructive(client, db, aluno, usar_llm):
    secretaria = make_user(db, Role.SECRETARIA)
    fake = usar_llm(chamar("excluir_aluno", aluno_id=aluno.id), texto("não posso"))
    headers = headers_of(secretaria)
    conversa_id = _nova_conversa(client, headers)
    _enviar(client, headers, conversa_id)
    assert "FERRAMENTA_INDISPONIVEL" in fake.ultimas_mensagens_tool()[0]["content"]

    admin = make_user(db, Role.ADMIN)
    usar_llm(chamar("excluir_aluno", aluno_id=aluno.id), texto("aguardando"))
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id)
    acao = next(m for m in resp.json()["mensagens"] if m["role"] == "acao")["acao"]
    assert acao["destrutiva"] is True

    assert client.post(f"{BASE}/acoes/{acao['id']}/confirmar", headers=headers).status_code == 200
    from app.modules.pessoas.models import Aluno

    assert db.get(Aluno, aluno.id).deleted_at is not None


# --- Limites e falhas -------------------------------------------------------------------------


def test_rate_limit_per_user(client, admin, usar_llm):
    usar_llm(*[texto("ok") for _ in range(12)])
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    codigos = [_enviar(client, headers, conversa_id).status_code for _ in range(11)]
    assert codigos[:10] == [200] * 10
    assert codigos[10] == 429


def test_llm_unavailable_returns_502_and_keeps_user_message(client, admin, app):
    from app.modules.assistente import service
    from app.modules.assistente.llm import LLMIndisponivelError

    class Quebrado:
        def chat(self, messages, tools):
            raise LLMIndisponivelError()

    app.dependency_overrides[service.get_llm_client] = lambda: Quebrado()
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    resp = _enviar(client, headers, conversa_id, "olá")
    assert resp.status_code == 502
    assert resp.json()["code"] == "LLM_INDISPONIVEL"
    detalhe = client.get(f"{BASE}/conversas/{conversa_id}", headers=headers).json()
    assert [m["role"] for m in detalhe["mensagens"]] == ["user"]


def test_message_validation(client, admin):
    headers = headers_of(admin)
    conversa_id = _nova_conversa(client, headers)
    assert _enviar(client, headers, conversa_id, "").status_code == 422
    assert _enviar(client, headers, conversa_id, "x" * 2001).status_code == 422
