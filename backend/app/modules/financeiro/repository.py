from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.financeiro.models import Bolsa, Cobranca, StatusCobranca, TabelaPreco, TipoCobranca


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()


def delete(db: Session, entity: object) -> None:
    db.delete(entity)
    db.flush()


# --- Cobrancas -----------------------------------------------------------------------------


def get_cobranca(db: Session, cobranca_id: int) -> Cobranca | None:
    return db.get(Cobranca, cobranca_id)


def find_mensalidade(db: Session, aluno_id: int, competencia: str) -> Cobranca | None:
    return db.scalar(
        select(Cobranca).where(
            Cobranca.aluno_id == aluno_id,
            Cobranca.tipo == TipoCobranca.MENSALIDADE,
            Cobranca.competencia == competencia,
        )
    )


def _cobrancas_stmt(
    *, aluno_id: int | None, aluno_ids: list[int] | None, status: StatusCobranca | None
) -> Select[tuple[Cobranca]]:
    stmt = select(Cobranca)
    if aluno_id is not None:
        stmt = stmt.where(Cobranca.aluno_id == aluno_id)
    elif aluno_ids is not None:
        stmt = stmt.where(Cobranca.aluno_id.in_(aluno_ids))
    if status is not None:
        stmt = stmt.where(Cobranca.status == status)
    return stmt.order_by(Cobranca.vencimento.desc())


def list_cobrancas(
    db: Session,
    *,
    aluno_id: int | None,
    aluno_ids: list[int] | None,
    status: StatusCobranca | None,
    limit: int,
    offset: int,
) -> tuple[list[Cobranca], int]:
    stmt = _cobrancas_stmt(aluno_id=aluno_id, aluno_ids=aluno_ids, status=status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return list(rows), total


def list_pendentes_vencidas(db: Session, aluno_id: int, data_limite: date) -> list[Cobranca]:
    stmt = select(Cobranca).where(
        Cobranca.aluno_id == aluno_id,
        Cobranca.status == StatusCobranca.PENDENTE,
        Cobranca.vencimento < data_limite,
    )
    return list(db.scalars(stmt).all())


# --- Bolsas --------------------------------------------------------------------------------


def get_bolsa(db: Session, bolsa_id: int) -> Bolsa | None:
    return db.get(Bolsa, bolsa_id)


def list_bolsas(db: Session, *, aluno_id: int | None) -> list[Bolsa]:
    stmt = select(Bolsa)
    if aluno_id is not None:
        stmt = stmt.where(Bolsa.aluno_id == aluno_id)
    return list(db.scalars(stmt.order_by(Bolsa.vigencia_inicio.desc())).all())


def list_bolsas_vigentes(db: Session, aluno_id: int, data_referencia: date) -> list[Bolsa]:
    stmt = select(Bolsa).where(
        Bolsa.aluno_id == aluno_id,
        Bolsa.vigencia_inicio <= data_referencia,
        (Bolsa.vigencia_fim.is_(None)) | (Bolsa.vigencia_fim >= data_referencia),
    )
    return list(db.scalars(stmt).all())


# --- Tabela de preços ----------------------------------------------------------------------


def get_preco(db: Session, preco_id: int) -> TabelaPreco | None:
    return db.get(TabelaPreco, preco_id)


def find_preco(db: Session, serie: str, ano_letivo: int) -> TabelaPreco | None:
    return db.scalar(
        select(TabelaPreco).where(TabelaPreco.serie == serie, TabelaPreco.ano_letivo == ano_letivo)
    )


def find_preco_by_ano(db: Session, ano_letivo: int) -> TabelaPreco | None:
    """Usado na geração de mensalidades simplificada: ignora a série, pega qualquer preço do ano."""
    return db.scalar(select(TabelaPreco).where(TabelaPreco.ano_letivo == ano_letivo).limit(1))


def list_precos(db: Session) -> list[TabelaPreco]:
    return list(db.scalars(select(TabelaPreco).order_by(TabelaPreco.ano_letivo.desc())).all())
