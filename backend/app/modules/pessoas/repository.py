from typing import Any

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.pessoas.models import Aluno, Funcionario, Professor, Responsavel, ResponsavelAluno


def _paginate[T](db: Session, stmt: Select[T], limit: int, offset: int) -> tuple[list[T], int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return list(rows), total


def _busca(nome_col: Any, cpf_col: Any, busca: str | None) -> ColumnElement[bool] | None:
    """Filtro por parte do nome ou pelo CPF completo (com ou sem pontuação)."""
    if not busca:
        return None
    digits = "".join(c for c in busca if c.isdigit())
    conditions = [nome_col.ilike(f"%{busca}%")]
    if len(digits) == 11:
        conditions.append(cpf_col == digits)
    return or_(*conditions)


# --- Alunos ------------------------------------------------------------------------------


def get_aluno(db: Session, aluno_id: int, *, include_deleted: bool = False) -> Aluno | None:
    stmt = (
        select(Aluno)
        .where(Aluno.id == aluno_id)
        .options(selectinload(Aluno.vinculos).selectinload(ResponsavelAluno.responsavel))
    )
    if not include_deleted:
        stmt = stmt.where(Aluno.deleted_at.is_(None))
    return db.scalar(stmt)


def get_aluno_by_cpf(db: Session, cpf: str) -> Aluno | None:
    return db.scalar(select(Aluno).where(Aluno.cpf == cpf, Aluno.deleted_at.is_(None)))


def list_alunos(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> tuple[list[Aluno], int]:
    stmt = select(Aluno).where(Aluno.deleted_at.is_(None)).order_by(Aluno.nome)
    condition = _busca(Aluno.nome, Aluno.cpf, busca)
    if condition is not None:
        stmt = stmt.where(condition)
    return _paginate(db, stmt, limit, offset)


def list_alunos_by_ids(
    db: Session, aluno_ids: list[int], *, include_deleted: bool = False
) -> list[Aluno]:
    if not aluno_ids:
        return []
    stmt = (
        select(Aluno)
        .where(Aluno.id.in_(aluno_ids))
        .options(selectinload(Aluno.vinculos).selectinload(ResponsavelAluno.responsavel))
        .order_by(Aluno.nome)
    )
    if not include_deleted:
        stmt = stmt.where(Aluno.deleted_at.is_(None))
    return list(db.scalars(stmt).all())


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()


# --- Vínculos ----------------------------------------------------------------------------


def get_vinculo(db: Session, aluno_id: int, responsavel_id: int) -> ResponsavelAluno | None:
    return db.get(ResponsavelAluno, (responsavel_id, aluno_id))


def list_vinculos_do_aluno(db: Session, aluno_id: int) -> list[ResponsavelAluno]:
    stmt = (
        select(ResponsavelAluno)
        .where(ResponsavelAluno.aluno_id == aluno_id)
        .options(selectinload(ResponsavelAluno.responsavel))
    )
    return list(db.scalars(stmt).all())


def list_aluno_ids_do_responsavel(
    db: Session, responsavel_id: int, *, include_deleted: bool = False
) -> list[int]:
    stmt = (
        select(ResponsavelAluno.aluno_id)
        .join(Aluno, Aluno.id == ResponsavelAluno.aluno_id)
        .where(ResponsavelAluno.responsavel_id == responsavel_id)
    )
    if not include_deleted:
        stmt = stmt.where(Aluno.deleted_at.is_(None))
    return list(db.scalars(stmt).all())


def delete_vinculo(db: Session, vinculo: ResponsavelAluno) -> None:
    db.delete(vinculo)
    db.flush()


# --- Responsáveis ------------------------------------------------------------------------


def get_responsavel(db: Session, responsavel_id: int) -> Responsavel | None:
    return db.scalar(
        select(Responsavel).where(
            Responsavel.id == responsavel_id, Responsavel.deleted_at.is_(None)
        )
    )


def get_responsavel_by_cpf(db: Session, cpf: str) -> Responsavel | None:
    return db.scalar(
        select(Responsavel).where(Responsavel.cpf == cpf, Responsavel.deleted_at.is_(None))
    )


def get_responsavel_by_user_id(db: Session, user_id: int) -> Responsavel | None:
    return db.scalar(
        select(Responsavel).where(Responsavel.user_id == user_id, Responsavel.deleted_at.is_(None))
    )


def list_responsaveis(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> tuple[list[Responsavel], int]:
    stmt = select(Responsavel).where(Responsavel.deleted_at.is_(None)).order_by(Responsavel.nome)
    condition = _busca(Responsavel.nome, Responsavel.cpf, busca)
    if condition is not None:
        stmt = stmt.where(condition)
    return _paginate(db, stmt, limit, offset)


def list_responsaveis_by_ids(db: Session, ids: list[int]) -> list[Responsavel]:
    if not ids:
        return []
    return list(db.scalars(select(Responsavel).where(Responsavel.id.in_(ids))).all())


# --- Professores -------------------------------------------------------------------------


def get_professor(db: Session, professor_id: int) -> Professor | None:
    return db.scalar(
        select(Professor).where(Professor.id == professor_id, Professor.deleted_at.is_(None))
    )


def get_professor_by_cpf(db: Session, cpf: str) -> Professor | None:
    return db.scalar(select(Professor).where(Professor.cpf == cpf, Professor.deleted_at.is_(None)))


def get_professor_by_user_id(db: Session, user_id: int) -> Professor | None:
    return db.scalar(
        select(Professor).where(Professor.user_id == user_id, Professor.deleted_at.is_(None))
    )


def list_professores(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> tuple[list[Professor], int]:
    stmt = select(Professor).where(Professor.deleted_at.is_(None)).order_by(Professor.nome)
    condition = _busca(Professor.nome, Professor.cpf, busca)
    if condition is not None:
        stmt = stmt.where(condition)
    return _paginate(db, stmt, limit, offset)


def list_professores_by_ids(db: Session, ids: list[int]) -> list[Professor]:
    if not ids:
        return []
    return list(db.scalars(select(Professor).where(Professor.id.in_(ids))).all())


# --- Funcionários ------------------------------------------------------------------------


def get_funcionario(db: Session, funcionario_id: int) -> Funcionario | None:
    return db.scalar(
        select(Funcionario).where(
            Funcionario.id == funcionario_id, Funcionario.deleted_at.is_(None)
        )
    )


def get_funcionario_by_cpf(db: Session, cpf: str) -> Funcionario | None:
    return db.scalar(
        select(Funcionario).where(Funcionario.cpf == cpf, Funcionario.deleted_at.is_(None))
    )


def list_funcionarios(
    db: Session, *, busca: str | None, limit: int, offset: int
) -> tuple[list[Funcionario], int]:
    stmt = select(Funcionario).where(Funcionario.deleted_at.is_(None)).order_by(Funcionario.nome)
    condition = _busca(Funcionario.nome, Funcionario.cpf, busca)
    if condition is not None:
        stmt = stmt.where(condition)
    return _paginate(db, stmt, limit, offset)
