from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DbSession, require_roles
from app.modules.turmas import permissions, service
from app.modules.turmas.schemas import ProfessorDaTurma, TurmaCreate, TurmaRead, TurmaUpdate
from app.shared.serie import Serie

router = APIRouter(prefix="/api/v1/turmas", tags=["turmas"])


@router.get("", response_model=list[TurmaRead])
def list_turmas(
    db: DbSession,
    ano_letivo: Annotated[int | None, Query()] = None,
    serie: Annotated[Serie | None, Query()] = None,
    ativa: Annotated[bool | None, Query()] = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_READ_TURMAS)),
) -> list[TurmaRead]:
    return service.list_turmas(db, ano_letivo=ano_letivo, serie=serie, ativa=ativa)


@router.post("", response_model=TurmaRead, status_code=status.HTTP_201_CREATED)
def create_turma(
    payload: TurmaCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_TURMAS)),
) -> TurmaRead:
    return service.create_turma(db, payload)


@router.get("/minhas", response_model=list[TurmaRead])
def list_minhas_turmas(
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_VIEW_OWN_TURMAS)),
) -> list[TurmaRead]:
    return service.list_minhas_turmas(db, user)


@router.get("/{turma_id}", response_model=TurmaRead)
def get_turma(
    turma_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_VIEW_TURMA)),
) -> TurmaRead:
    return service.get_turma(db, turma_id, user)


@router.patch("/{turma_id}", response_model=TurmaRead)
def update_turma(
    turma_id: int,
    payload: TurmaUpdate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_TURMAS)),
) -> TurmaRead:
    return service.update_turma(db, turma_id, payload)


@router.post("/{turma_id}/professores", response_model=TurmaRead)
def add_professor(
    turma_id: int,
    payload: ProfessorDaTurma,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_TURMAS)),
) -> TurmaRead:
    return service.add_professor(db, turma_id, payload.professor_id)


@router.delete("/{turma_id}/professores/{professor_id}", response_model=TurmaRead)
def remove_professor(
    turma_id: int,
    professor_id: int,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_TURMAS)),
) -> TurmaRead:
    return service.remove_professor(db, turma_id, professor_id)
