"""Regras do calendário: visibilidade geral de leitura e permissões finas de escrita."""

from datetime import date

from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.core.roles import Role
from app.modules.calendario import repository
from app.modules.calendario.models import EventoCalendario
from app.modules.calendario.schemas import (
    EventoCalendarioCreate,
    EventoCalendarioRead,
    EventoCalendarioUpdate,
)
from app.modules.turmas import service as turmas_service

EVENTO_NAO_ENCONTRADO = "Evento não encontrado."


def _get_or_404(db: Session, evento_id: int) -> EventoCalendario:
    evento = repository.get(db, evento_id)
    if evento is None:
        raise NotFoundError(EVENTO_NAO_ENCONTRADO)
    return evento


def _pode_editar(user: CurrentUser, evento: EventoCalendario) -> bool:
    if user.role in (Role.ADMIN, Role.SECRETARIA):
        return True
    return evento.criado_por_user_id == user.id


# --- Casos de uso ------------------------------------------------------------------------


def list_eventos(
    db: Session, *, de: date, ate: date, turma_id: int | None
) -> list[EventoCalendarioRead]:
    eventos = repository.list_periodo(db, de=de, ate=ate, turma_id=turma_id)
    return [EventoCalendarioRead.model_validate(e) for e in eventos]


def create_evento(
    db: Session, data: EventoCalendarioCreate, user: CurrentUser
) -> EventoCalendarioRead:
    if user.role == Role.PROFESSOR:
        if data.turma_id is None or not turmas_service.is_professor_da_turma(
            db, data.turma_id, user.id
        ):
            raise ForbiddenError(
                "Professores só podem criar eventos para turmas em que lecionam."
            )
    elif data.turma_id is not None:
        # Garante que a turma existe (404 se não); ADMIN/SECRETARIA podem criar eventos
        # gerais ou de qualquer turma.
        turmas_service.get_turma_read(db, data.turma_id)

    evento = EventoCalendario(**data.model_dump(), criado_por_user_id=user.id)
    repository.add(db, evento)
    db.commit()
    return EventoCalendarioRead.model_validate(evento)


def update_evento(
    db: Session, evento_id: int, data: EventoCalendarioUpdate, user: CurrentUser
) -> EventoCalendarioRead:
    evento = _get_or_404(db, evento_id)
    if not _pode_editar(user, evento):
        raise ForbiddenError("Você não tem permissão para editar este evento.")

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(evento, field, value)

    # Revalida o intervalo após aplicar as alterações (datas podem ter sido parciais).
    if evento.data_fim is not None and evento.data_fim < evento.data_inicio:
        raise BusinessRuleError(
            "data_fim não pode ser anterior a data_inicio.", "INTERVALO_INVALIDO"
        )

    db.commit()
    return EventoCalendarioRead.model_validate(evento)


def delete_evento(db: Session, evento_id: int, user: CurrentUser) -> None:
    evento = _get_or_404(db, evento_id)
    if not _pode_editar(user, evento):
        raise ForbiddenError("Você não tem permissão para excluir este evento.")
    repository.delete(db, evento)
    db.commit()
