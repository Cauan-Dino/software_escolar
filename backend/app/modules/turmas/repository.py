from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.turmas.models import Turma, TurmaProfessor
from app.shared.serie import Serie, Turno


def get_turma(db: Session, turma_id: int) -> Turma | None:
    return db.get(Turma, turma_id)


def get_turma_for_update(db: Session, turma_id: int) -> Turma | None:
    """SELECT ... FOR UPDATE: trava a linha até o fim da transação.

    Duas aprovações simultâneas na mesma turma ficam em fila aqui, então a segunda já
    enxerga a vaga ocupada pela primeira.
    """
    stmt = (
        select(Turma)
        .where(Turma.id == turma_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return db.scalar(stmt)


def find_turma(db: Session, serie: Serie, ano_letivo: int, turno: Turno) -> Turma | None:
    return db.scalar(
        select(Turma).where(
            Turma.serie == serie, Turma.ano_letivo == ano_letivo, Turma.turno == turno
        )
    )


def list_turmas(
    db: Session,
    *,
    ano_letivo: int | None = None,
    serie: Serie | None = None,
    ativa: bool | None = None,
    turma_ids: list[int] | None = None,
) -> list[Turma]:
    stmt = select(Turma)
    if ano_letivo is not None:
        stmt = stmt.where(Turma.ano_letivo == ano_letivo)
    if serie is not None:
        stmt = stmt.where(Turma.serie == serie)
    if ativa is not None:
        stmt = stmt.where(Turma.ativa == ativa)
    if turma_ids is not None:
        stmt = stmt.where(Turma.id.in_(turma_ids))
    return list(db.scalars(stmt.order_by(Turma.ano_letivo.desc(), Turma.serie, Turma.turno)).all())


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()


def list_professor_ids(db: Session, turma_id: int) -> list[int]:
    stmt = select(TurmaProfessor.professor_id).where(TurmaProfessor.turma_id == turma_id)
    return list(db.scalars(stmt).all())


def list_turma_ids_do_professor(db: Session, professor_id: int) -> list[int]:
    stmt = select(TurmaProfessor.turma_id).where(TurmaProfessor.professor_id == professor_id)
    return list(db.scalars(stmt).all())


def get_turma_professor(db: Session, turma_id: int, professor_id: int) -> TurmaProfessor | None:
    return db.get(TurmaProfessor, (turma_id, professor_id))


def delete(db: Session, entity: object) -> None:
    db.delete(entity)
    db.flush()
