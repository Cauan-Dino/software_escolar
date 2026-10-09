"""Regras de frequência (chamada/presença).

Alunos da turma são obtidos via `matricula.service.list_aluno_ids_ativos_da_turma`
(só matrículas ATIVA contam) + `pessoas.service.list_alunos_reads` (nomes).
"""

from datetime import date

from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.frequencia import repository
from app.modules.frequencia.models import Frequencia
from app.modules.frequencia.schemas import (
    STATUS_CONTAM_PRESENCA,
    AlunoChamada,
    CorrigirRegistro,
    FrequenciaRead,
    HistoricoFrequencia,
    LancarChamada,
    StatusFrequencia,
)
from app.modules.matricula import service as matricula_service
from app.modules.pessoas import service as pessoas_service
from app.modules.turmas import service as turmas_service

ALUNO_NAO_MATRICULADO = "Aluno não está matriculado (ativo) nesta turma."


def _ensure_pode_lancar_na_turma(db: Session, turma_id: int, user: CurrentUser) -> None:
    """Garante acesso à turma: PROFESSOR só lança/vê se leciona nela; equipe sempre pode."""
    turmas_service.get_turma_read(db, turma_id)  # 404 se a turma não existir
    if user.role == Role.PROFESSOR and not turmas_service.is_professor_da_turma(
        db, turma_id, user.id
    ):
        raise ForbiddenError("Você não leciona nesta turma.")


def _alunos_ativos_da_turma(db: Session, turma_id: int) -> list[tuple[int, str]]:
    aluno_ids = matricula_service.list_aluno_ids_ativos_da_turma(db, turma_id)
    alunos = pessoas_service.list_alunos_reads(db, aluno_ids)
    nomes = {a.id: a.nome for a in alunos}
    return [(aid, nomes.get(aid, "—")) for aid in aluno_ids]


# --- Casos de uso --------------------------------------------------------------------------


def get_chamada_do_dia(
    db: Session, turma_id: int, data: date, user: CurrentUser
) -> list[AlunoChamada]:
    _ensure_pode_lancar_na_turma(db, turma_id, user)
    alunos = _alunos_ativos_da_turma(db, turma_id)
    lancados = {f.aluno_id: f for f in repository.list_by_turma_data(db, turma_id, data)}
    resultado: list[AlunoChamada] = []
    for aluno_id, nome in alunos:
        registro = lancados.get(aluno_id)
        if registro is not None:
            resultado.append(
                AlunoChamada(
                    aluno_id=aluno_id,
                    aluno_nome=nome,
                    status=registro.status,
                    observacao=registro.observacao,
                    lancado=True,
                )
            )
        else:
            resultado.append(
                AlunoChamada(
                    aluno_id=aluno_id,
                    aluno_nome=nome,
                    status=StatusFrequencia.PRESENTE,
                    observacao=None,
                    lancado=False,
                )
            )
    return resultado


def lancar_chamada(
    db: Session, turma_id: int, data: date, payload: LancarChamada, user: CurrentUser
) -> list[FrequenciaRead]:
    _ensure_pode_lancar_na_turma(db, turma_id, user)
    alunos_validos = {aid for aid, _ in _alunos_ativos_da_turma(db, turma_id)}

    resultado: list[Frequencia] = []
    for registro in payload.registros:
        if registro.aluno_id not in alunos_validos:
            raise NotFoundError(ALUNO_NAO_MATRICULADO)
        existente = repository.get_by_aluno_data(db, registro.aluno_id, data)
        if existente is not None:
            existente.status = registro.status
            existente.observacao = registro.observacao
            existente.turma_id = turma_id
            existente.lancado_por_user_id = user.id
            resultado.append(existente)
        else:
            novo = Frequencia(
                aluno_id=registro.aluno_id,
                turma_id=turma_id,
                data=data,
                status=registro.status,
                observacao=registro.observacao,
                lancado_por_user_id=user.id,
            )
            repository.add(db, novo)
            resultado.append(novo)
    db.commit()
    return [FrequenciaRead.model_validate(f) for f in resultado]


def corrigir_registro(
    db: Session,
    turma_id: int,
    aluno_id: int,
    data: date,
    payload: CorrigirRegistro,
    user: CurrentUser,
) -> FrequenciaRead:
    _ensure_pode_lancar_na_turma(db, turma_id, user)
    alunos_validos = {aid for aid, _ in _alunos_ativos_da_turma(db, turma_id)}
    if aluno_id not in alunos_validos:
        raise NotFoundError(ALUNO_NAO_MATRICULADO)

    registro = repository.get_by_aluno_data(db, aluno_id, data)
    if registro is None:
        registro = Frequencia(
            aluno_id=aluno_id,
            turma_id=turma_id,
            data=data,
            status=payload.status,
            observacao=payload.observacao,
            lancado_por_user_id=user.id,
        )
        repository.add(db, registro)
    else:
        registro.status = payload.status
        registro.observacao = payload.observacao
        registro.lancado_por_user_id = user.id
    db.commit()
    return FrequenciaRead.model_validate(registro)


def get_historico_do_aluno(
    db: Session, aluno_id: int, de: date, ate: date, user: CurrentUser
) -> HistoricoFrequencia:
    if user.role in (Role.RESPONSAVEL, Role.ALUNO):
        pessoas_service.ensure_can_access_aluno(db, user, aluno_id)
    else:
        # Equipe (STAFF) e PROFESSOR veem qualquer aluno; só valida que ele existe.
        pessoas_service.get_aluno_read(db, aluno_id)

    registros = repository.list_by_aluno_periodo(db, aluno_id, de, ate)
    total = len(registros)
    presencas = sum(1 for r in registros if r.status in STATUS_CONTAM_PRESENCA)
    percentual = round((presencas / total) * 100, 1) if total else 0.0
    return HistoricoFrequencia(
        aluno_id=aluno_id,
        de=de,
        ate=ate,
        percentual_presenca=percentual,
        registros=[FrequenciaRead.model_validate(r) for r in registros],
    )
