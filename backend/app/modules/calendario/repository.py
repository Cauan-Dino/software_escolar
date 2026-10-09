from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.calendario.models import EventoCalendario


def get(db: Session, evento_id: int) -> EventoCalendario | None:
    return db.get(EventoCalendario, evento_id)


def list_periodo(
    db: Session, *, de: date, ate: date, turma_id: int | None = None
) -> list[EventoCalendario]:
    """Eventos cujo intervalo [data_inicio, data_fim ou data_inicio] toca [de, ate]."""
    fim_efetivo = func.coalesce(EventoCalendario.data_fim, EventoCalendario.data_inicio)
    stmt = select(EventoCalendario).where(
        EventoCalendario.data_inicio <= ate,
        fim_efetivo >= de,
    )
    if turma_id is not None:
        stmt = stmt.where(
            or_(EventoCalendario.turma_id == turma_id, EventoCalendario.turma_id.is_(None))
        )
    return list(db.scalars(stmt.order_by(EventoCalendario.data_inicio)).all())


def add(db: Session, entity: EventoCalendario) -> None:
    db.add(entity)
    db.flush()


def delete(db: Session, entity: EventoCalendario) -> None:
    db.delete(entity)
    db.flush()
