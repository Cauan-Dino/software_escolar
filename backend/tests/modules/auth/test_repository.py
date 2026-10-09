from datetime import UTC, datetime, timedelta

from app.core.roles import Role
from app.modules.auth import repository
from app.modules.auth.models import RefreshToken
from tests.factories import make_user


def test_get_user_by_email_is_case_insensitive(db):
    user = make_user(db, email="maria@escola.com")
    assert repository.get_user_by_email(db, "MARIA@Escola.com") == user
    assert repository.get_user_by_email(db, "ninguem@escola.com") is None


def test_list_users_filters_by_role_and_paginates(db):
    make_user(db, Role.PROFESSOR)
    make_user(db, Role.PROFESSOR)
    make_user(db, Role.FINANCEIRO)
    rows, total = repository.list_users(db, role=Role.PROFESSOR, limit=1, offset=0)
    assert total == 2
    assert len(rows) == 1
    assert rows[0].role == Role.PROFESSOR


def test_refresh_tokens_can_be_found_and_revoked_in_bulk(db):
    user = make_user(db)
    expires = datetime.now(UTC) + timedelta(days=1)
    for jti in ("a", "b"):
        repository.add_refresh_token(db, RefreshToken(user_id=user.id, jti=jti, expires_at=expires))
    assert repository.get_refresh_token_by_jti(db, "a") is not None
    now = datetime.now(UTC)
    repository.revoke_all_refresh_tokens(db, user.id, now)
    db.expire_all()
    token = repository.get_refresh_token_by_jti(db, "b")
    assert token is not None
    assert token.revoked_at is not None
