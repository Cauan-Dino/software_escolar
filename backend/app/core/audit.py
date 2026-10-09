"""Trilha de auditoria (tabela `audit_log`): quem fez, quando, o quê, em qual entidade,
e o estado antes/depois.

Obrigatória para: aprovar/rejeitar matrícula, conceder bolsa, baixar pagamento e alterar
estoque. Chame `record_audit(...)` dentro do service, na mesma transação da operação.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import JSON, DateTime, String, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base
from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.roles import Role
from app.shared.pagination import Page, Pagination
from app.shared.schemas import OutputSchema

JsonDict = dict[str, Any]


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Sem FK de propósito: o log precisa sobreviver mesmo que o usuário seja removido.
    actor_user_id: Mapped[int | None] = mapped_column(index=True)
    actor_role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(50), index=True)
    before: Mapped[JsonDict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    after: Mapped[JsonDict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


def _to_json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _to_json_value(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_to_json_value(v) for v in value]
    return value


def snapshot(obj: object, fields: list[str]) -> JsonDict:
    """Foto serializável dos campos de um objeto, para `before`/`after`."""
    return {field: _to_json_value(getattr(obj, field)) for field in fields}


def record_audit(
    db: Session,
    *,
    actor: CurrentUser | None,
    action: str,
    entity: str,
    entity_id: int | str,
    before: JsonDict | None = None,
    after: JsonDict | None = None,
) -> AuditLog:
    """Registra uma entrada de auditoria. `actor=None` significa ação do sistema (ex.: webhook).

    Não faz commit: participa da transação de quem chamou.
    """
    entry = AuditLog(
        actor_user_id=actor.id if actor else None,
        actor_role=actor.role.value if actor else "SISTEMA",
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        before=_to_json_value(before) if before is not None else None,
        after=_to_json_value(after) if after is not None else None,
    )
    db.add(entry)
    db.flush()
    return entry


# --- Leitura (somente ADMIN) -------------------------------------------------------------


class AuditLogRead(OutputSchema):
    id: int
    actor_user_id: int | None
    actor_role: str | None
    action: str
    entity: str
    entity_id: str
    before: JsonDict | None
    after: JsonDict | None
    created_at: datetime


def list_audit_logs(
    db: Session,
    *,
    entity: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).offset(offset)
    ).all()
    return list(rows), total


router = APIRouter(prefix="/api/v1/auditoria", tags=["auditoria"])


@router.get("", response_model=Page[AuditLogRead])
def get_audit_logs(
    db: DbSession,
    page: Pagination,
    entity: Annotated[str | None, Query()] = None,
    entity_id: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    _: CurrentUser = Depends(require_roles(Role.ADMIN)),
) -> Page[AuditLogRead]:
    rows, total = list_audit_logs(
        db, entity=entity, entity_id=entity_id, action=action, limit=page.limit, offset=page.offset
    )
    return Page[AuditLogRead](
        items=[AuditLogRead.model_validate(r) for r in rows],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
