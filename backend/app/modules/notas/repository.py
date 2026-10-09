from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notas.models import Nota
from app.modules.notas.schemas import Periodo


def get_nota(
    db: Session, aluno_id: int, turma_id: int, disciplina: str, periodo: Periodo
) -> Nota | None:
    stmt = select(Nota).where(
        Nota.aluno_id == aluno_id,
        Nota.turma_id == turma_id,
        Nota.disciplina == disciplina,
        Nota.periodo == periodo,
    )
    return db.scalar(stmt)


def list_notas_turma(db: Session, turma_id: int, periodo: Periodo) -> list[Nota]:
    stmt = select(Nota).where(Nota.turma_id == turma_id, Nota.periodo == periodo)
    return list(db.scalars(stmt).all())


def list_notas_aluno(db: Session, aluno_id: int) -> list[Nota]:
    stmt = select(Nota).where(Nota.aluno_id == aluno_id)
    return list(db.scalars(stmt).all())


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()
