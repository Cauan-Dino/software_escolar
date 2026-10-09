from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DbSession, get_current_user, require_roles
from app.modules.calendario import permissions, service
from app.modules.calendario.schemas import (
    EventoCalendarioCreate,
    EventoCalendarioRead,
    EventoCalendarioUpdate,
)

router = APIRouter(prefix="/api/v1/calendario", tags=["calendario"])


@router.get("/eventos", response_model=list[EventoCalendarioRead])
def list_eventos(
    db: DbSession,
    de: Annotated[date | None, Query()] = None,
    ate: Annotated[date | None, Query()] = None,
    turma_id: Annotated[int | None, Query()] = None,
    _: CurrentUser = Depends(get_current_user),
) -> list[EventoCalendarioRead]:
    hoje = date.today()
    periodo_de = de or hoje
    periodo_ate = ate or (periodo_de + timedelta(days=60))
    return service.list_eventos(db, de=periodo_de, ate=periodo_ate, turma_id=turma_id)


@router.post("/eventos", response_model=EventoCalendarioRead, status_code=status.HTTP_201_CREATED)
def create_evento(
    payload: EventoCalendarioCreate,
    db: DbSession,
    user: CurrentUser = Depends(require_roles(*permissions.CAN_CREATE_EVENTO)),
) -> EventoCalendarioRead:
    return service.create_evento(db, payload, user)


@router.patch("/eventos/{evento_id}", response_model=EventoCalendarioRead)
def update_evento(
    evento_id: int,
    payload: EventoCalendarioUpdate,
    db: DbSession,
    user: CurrentUser = Depends(get_current_user),
) -> EventoCalendarioRead:
    return service.update_evento(db, evento_id, payload, user)


@router.delete("/eventos/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evento(
    evento_id: int,
    db: DbSession,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    service.delete_evento(db, evento_id, user)
