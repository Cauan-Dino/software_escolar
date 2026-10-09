from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.frequencia.models import Frequencia


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()


def get_by_aluno_data(db: Session, aluno_id: int, data: date) -> Frequencia | None:
    return db.scalar(
        select(Frequencia).where(Frequencia.aluno_id == aluno_id, Frequencia.data == data)
    )


def list_by_turma_data(db: Session, turma_id: int, data: date) -> list[Frequencia]:
    stmt = select(Frequencia).where(Frequencia.turma_id == turma_id, Frequencia.data == data)
    return list(db.scalars(stmt).all())


def list_by_aluno_periodo(db: Session, aluno_id: int, de: date, ate: date) -> list[Frequencia]:
    stmt = (
        select(Frequencia)
        .where(Frequencia.aluno_id == aluno_id, Frequencia.data >= de, Frequencia.data <= ate)
        .order_by(Frequencia.data)
    )
    return list(db.scalars(stmt).all())
