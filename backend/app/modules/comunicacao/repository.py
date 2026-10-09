from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.comunicacao.models import Aviso, LeituraAviso
from app.modules.comunicacao.schemas import PublicoAlvo


def get_aviso(db: Session, aviso_id: int) -> Aviso | None:
    return db.get(Aviso, aviso_id)


def _visibility_filter(stmt, *, publicos: list[PublicoAlvo], turma_ids: list[int]):
    conditions = [Aviso.publico_alvo.in_(publicos)]
    if turma_ids:
        conditions.append((Aviso.publico_alvo == PublicoAlvo.TURMA) & Aviso.turma_id.in_(turma_ids))
    from sqlalchemy import or_

    return stmt.where(or_(*conditions))


def list_avisos_visiveis(
    db: Session,
    *,
    ve_tudo: bool,
    publicos: list[PublicoAlvo],
    turma_ids: list[int],
    limit: int,
    offset: int,
) -> tuple[list[Aviso], int]:
    stmt = select(Aviso)
    if not ve_tudo:
        stmt = _visibility_filter(stmt, publicos=publicos, turma_ids=turma_ids)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Aviso.fixado.desc(), Aviso.publicado_em.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all()), total


def list_ids_visiveis_sem_leitura(
    db: Session,
    *,
    user_id: int,
    ve_tudo: bool,
    publicos: list[PublicoAlvo],
    turma_ids: list[int],
) -> int:
    stmt = select(func.count()).select_from(Aviso)
    if not ve_tudo:
        stmt = _visibility_filter(stmt, publicos=publicos, turma_ids=turma_ids)
    stmt = stmt.where(
        ~select(LeituraAviso.aviso_id)
        .where(LeituraAviso.aviso_id == Aviso.id, LeituraAviso.user_id == user_id)
        .exists()
    )
    return db.scalar(stmt) or 0


def list_leituras(db: Session, aviso_ids: list[int], user_id: int) -> set[int]:
    if not aviso_ids:
        return set()
    stmt = select(LeituraAviso.aviso_id).where(
        LeituraAviso.aviso_id.in_(aviso_ids), LeituraAviso.user_id == user_id
    )
    return set(db.scalars(stmt).all())


def marcar_lido(db: Session, aviso_id: int, user_id: int) -> None:
    stmt = (
        insert(LeituraAviso)
        .values(aviso_id=aviso_id, user_id=user_id)
        .on_conflict_do_nothing(index_elements=["aviso_id", "user_id"])
    )
    db.execute(stmt)
    db.flush()


def add(db: Session, entity: object) -> None:
    db.add(entity)
    db.flush()


def delete(db: Session, entity: object) -> None:
    db.delete(entity)
    db.flush()
