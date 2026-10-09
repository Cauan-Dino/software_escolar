from collections.abc import Collection

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.matricula.models import DocumentoMatricula, Matricula
from app.modules.matricula.schemas import STATUS_ENCERRADOS, StatusMatricula, TipoDocumento
from app.shared.serie import Serie


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()


def get_matricula(db: Session, matricula_id: int) -> Matricula | None:
    stmt = (
        select(Matricula)
        .where(Matricula.id == matricula_id)
        .options(selectinload(Matricula.documentos))
    )
    return db.scalar(stmt)


def get_em_aberto(db: Session, aluno_id: int, ano_letivo: int) -> Matricula | None:
    """Matrícula não rejeitada/cancelada do aluno naquele ano letivo."""
    return db.scalar(
        select(Matricula).where(
            Matricula.aluno_id == aluno_id,
            Matricula.ano_letivo == ano_letivo,
            Matricula.status.not_in(STATUS_ENCERRADOS),
        )
    )


def list_matriculas(
    db: Session,
    *,
    status: StatusMatricula | None = None,
    ano_letivo: int | None = None,
    serie: Serie | None = None,
    turma_id: int | None = None,
    aluno_ids: Collection[int] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Matricula], int]:
    stmt = select(Matricula).options(selectinload(Matricula.documentos))
    if status is not None:
        stmt = stmt.where(Matricula.status == status)
    if ano_letivo is not None:
        stmt = stmt.where(Matricula.ano_letivo == ano_letivo)
    if serie is not None:
        stmt = stmt.where(Matricula.serie == serie)
    if turma_id is not None:
        stmt = stmt.where(Matricula.turma_id == turma_id)
    if aluno_ids is not None:
        stmt = stmt.where(Matricula.aluno_id.in_(list(aluno_ids)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Matricula.created_at.desc(), Matricula.id.desc()).limit(limit).offset(offset)
    ).all()
    return list(rows), total


def list_by_aluno(db: Session, aluno_id: int) -> list[Matricula]:
    stmt = (
        select(Matricula)
        .where(Matricula.aluno_id == aluno_id)
        .options(selectinload(Matricula.documentos))
        .order_by(Matricula.ano_letivo.desc(), Matricula.id.desc())
    )
    return list(db.scalars(stmt).all())


def list_aluno_ids_por_status_na_turma(
    db: Session, turma_id: int, statuses: Collection[StatusMatricula]
) -> list[int]:
    stmt = select(Matricula.aluno_id).where(
        Matricula.turma_id == turma_id, Matricula.status.in_(list(statuses))
    )
    return list(db.scalars(stmt).all())


def get_documento(
    db: Session, matricula_id: int, tipo: TipoDocumento
) -> DocumentoMatricula | None:
    return db.scalar(
        select(DocumentoMatricula).where(
            DocumentoMatricula.matricula_id == matricula_id, DocumentoMatricula.tipo == tipo
        )
    )
