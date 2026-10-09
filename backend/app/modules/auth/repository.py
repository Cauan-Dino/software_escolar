from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.roles import Role
from app.modules.auth.models import RefreshToken, User


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def add_user(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user


def list_users(
    db: Session, *, role: Role | None, limit: int, offset: int
) -> tuple[list[User], int]:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(User.nome).limit(limit).offset(offset)).all()
    return list(rows), total


def add_refresh_token(db: Session, token: RefreshToken) -> RefreshToken:
    db.add(token)
    db.flush()
    return token


def get_refresh_token_by_jti(db: Session, jti: str) -> RefreshToken | None:
    return db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))


def revoke_all_refresh_tokens(db: Session, user_id: int, now: datetime) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
