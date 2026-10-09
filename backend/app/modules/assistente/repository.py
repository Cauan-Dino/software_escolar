"""Queries do assistente. Não faz commit (o service decide)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assistente.models import AcaoPendente, Conversa, Mensagem, StatusAcao


def add(db: Session, obj: Conversa | Mensagem | AcaoPendente) -> None:
    db.add(obj)
    db.flush()


def get_conversa(db: Session, conversa_id: int, user_id: int) -> Conversa | None:
    return db.scalar(
        select(Conversa).where(Conversa.id == conversa_id, Conversa.user_id == user_id)
    )


def list_conversas(db: Session, user_id: int, limit: int = 30) -> list[Conversa]:
    stmt = (
        select(Conversa)
        .where(Conversa.user_id == user_id)
        .order_by(Conversa.updated_at.desc(), Conversa.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def delete_conversa(db: Session, conversa: Conversa) -> None:
    db.delete(conversa)
    db.flush()


def list_mensagens(db: Session, conversa_id: int) -> list[Mensagem]:
    stmt = select(Mensagem).where(Mensagem.conversa_id == conversa_id).order_by(Mensagem.id)
    return list(db.scalars(stmt))


def get_acao(
    db: Session, acao_id: str, user_id: int, *, for_update: bool = False
) -> AcaoPendente | None:
    stmt = select(AcaoPendente).where(AcaoPendente.id == acao_id, AcaoPendente.user_id == user_id)
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def list_acoes_da_conversa(db: Session, conversa_id: int) -> list[AcaoPendente]:
    stmt = select(AcaoPendente).where(AcaoPendente.conversa_id == conversa_id)
    return list(db.scalars(stmt))


def list_acoes_pendentes_vencidas(
    db: Session, conversa_id: int, agora: datetime
) -> list[AcaoPendente]:
    stmt = select(AcaoPendente).where(
        AcaoPendente.conversa_id == conversa_id,
        AcaoPendente.status == StatusAcao.PENDENTE,
        AcaoPendente.expira_em <= agora,
    )
    return list(db.scalars(stmt))
