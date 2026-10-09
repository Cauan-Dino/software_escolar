from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbSession, require_roles
from app.modules.comunicacao import permissions, service
from app.modules.comunicacao.schemas import AvisoCreate, AvisoRead, AvisoUpdate, NaoLidosTotal
from app.shared.pagination import Page, Pagination

router = APIRouter(prefix="/api/v1/comunicacao", tags=["comunicacao"])


@router.get("/avisos", response_model=Page[AvisoRead])
def list_avisos(
    db: DbSession,
    page: Pagination,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ_AVISOS)),
) -> Page[AvisoRead]:
    return service.list_avisos(db, user, limit=page.limit, offset=page.offset)


@router.get("/avisos/nao-lidos/total", response_model=NaoLidosTotal)
def contar_nao_lidos(
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ_AVISOS)),
) -> NaoLidosTotal:
    return service.contar_nao_lidos(db, user)


@router.post("/avisos", response_model=AvisoRead, status_code=status.HTTP_201_CREATED)
def create_aviso(
    payload: AvisoCreate,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_CREATE_AVISO)),
) -> AvisoRead:
    return service.create_aviso(db, payload, user)


@router.patch("/avisos/{aviso_id}", response_model=AvisoRead)
def update_aviso(
    aviso_id: int,
    payload: AvisoUpdate,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ_AVISOS)),
) -> AvisoRead:
    return service.update_aviso(db, aviso_id, payload, user)


@router.delete("/avisos/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aviso(
    aviso_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ_AVISOS)),
) -> None:
    service.delete_aviso(db, aviso_id, user)


@router.post("/avisos/{aviso_id}/lido", status_code=status.HTTP_204_NO_CONTENT)
def marcar_lido(
    aviso_id: int,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_READ_AVISOS)),
) -> None:
    service.marcar_lido(db, aviso_id, user)
