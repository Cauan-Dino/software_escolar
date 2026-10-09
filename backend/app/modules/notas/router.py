from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, get_current_user, require_roles
from app.modules.notas import permissions, service
from app.modules.notas.schemas import BoletimRead, NotaRead, NotaUpsert, Periodo, TurmaGradeRead

router = APIRouter(prefix="/api/v1/notas", tags=["notas"])


@router.get("/disciplinas", response_model=list[str])
def list_disciplinas(_: CurrentUser = Depends(get_current_user)) -> list[str]:
    return service.list_disciplinas()


@router.get("/turmas/{turma_id}", response_model=TurmaGradeRead)
def get_grade(
    turma_id: int,
    db: DbSession,
    periodo: Periodo = Query(...),
    user: CurrentUser = Depends(require_roles(*permissions.CAN_LANCAR_NOTAS)),
) -> TurmaGradeRead:
    return service.list_grade(db, turma_id, periodo, user)


@router.put("/turmas/{turma_id}/alunos/{aluno_id}", response_model=NotaRead)
def lancar_nota(
    turma_id: int,
    aluno_id: int,
    payload: NotaUpsert,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_LANCAR_NOTAS)),
) -> NotaRead:
    return service.upsert_nota(db, turma_id, aluno_id, payload, user)


@router.get("/alunos/{aluno_id}/boletim", response_model=BoletimRead)
def get_boletim(
    aluno_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_VER_BOLETIM)),
) -> BoletimRead:
    return service.get_boletim(db, aluno_id, user)
