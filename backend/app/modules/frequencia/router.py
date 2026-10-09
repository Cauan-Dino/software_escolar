from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.modules.frequencia import permissions, service
from app.modules.frequencia.schemas import (
    AlunoChamada,
    CorrigirRegistro,
    FrequenciaRead,
    HistoricoFrequencia,
    LancarChamada,
)
from app.shared import clock

router = APIRouter(prefix="/api/v1/frequencia", tags=["frequencia"])


@router.get("/turmas/{turma_id}", response_model=list[AlunoChamada])
def get_chamada_do_dia(
    turma_id: int,
    db: DbSession,
    data: Annotated[date | None, Query()] = None,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_LANCAR_FREQUENCIA)),
) -> list[AlunoChamada]:
    return service.get_chamada_do_dia(db, turma_id, data or clock.today(), user)


@router.post("/turmas/{turma_id}", response_model=list[FrequenciaRead])
def lancar_chamada(
    turma_id: int,
    payload: LancarChamada,
    db: DbSession,
    data: Annotated[date | None, Query()] = None,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_LANCAR_FREQUENCIA)),
) -> list[FrequenciaRead]:
    return service.lancar_chamada(db, turma_id, data or clock.today(), payload, user)


@router.patch("/turmas/{turma_id}/alunos/{aluno_id}", response_model=FrequenciaRead)
def corrigir_registro(
    turma_id: int,
    aluno_id: int,
    payload: CorrigirRegistro,
    db: DbSession,
    data: Annotated[date | None, Query()] = None,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_LANCAR_FREQUENCIA)),
) -> FrequenciaRead:
    return service.corrigir_registro(db, turma_id, aluno_id, data or clock.today(), payload, user)


@router.get("/alunos/{aluno_id}", response_model=HistoricoFrequencia)
def get_historico_do_aluno(
    aluno_id: int,
    de: Annotated[date, Query()],
    ate: Annotated[date, Query()],
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_VER_FREQUENCIA)),
) -> HistoricoFrequencia:
    return service.get_historico_do_aluno(db, aluno_id, de, ate, user)
