import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, UnauthorizedError
from app.core.roles import Role
from app.core.security import decode_token
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, PasswordChange, UserCreate, UserUpdate
from tests.factories import DEFAULT_PASSWORD, make_user
from tests.helpers import current_user


def login(db, email, password=DEFAULT_PASSWORD):
    return service.login(db, LoginRequest(email=email, password=password))


def test_login_returns_access_and_refresh_tokens(db):
    user = make_user(db, Role.SECRETARIA)
    tokens = login(db, user.email)
    assert decode_token(tokens.access_token, "access")["role"] == "SECRETARIA"
    assert decode_token(tokens.refresh_token, "refresh")["sub"] == str(user.id)
    assert tokens.user.id == user.id
    assert user.last_login_at is not None


@pytest.mark.parametrize("password", ["errada123", ""])
def test_login_with_wrong_password_fails_generically(db, password):
    user = make_user(db)
    with pytest.raises((UnauthorizedError, ValueError)):
        login(db, user.email, password or "x")


def test_login_with_unknown_email_has_same_error_as_wrong_password(db):
    with pytest.raises(UnauthorizedError) as unknown:
        login(db, "naoexiste@teste.com")
    user = make_user(db)
    with pytest.raises(UnauthorizedError) as wrong:
        login(db, user.email, "errada123")
    assert unknown.value.detail == wrong.value.detail
    assert unknown.value.code == wrong.value.code == "INVALID_CREDENTIALS"


def test_inactive_user_cannot_login(db):
    user = make_user(db, is_active=False)
    with pytest.raises(UnauthorizedError):
        login(db, user.email)


def test_refresh_rotates_token_and_old_one_stops_working(db):
    user = make_user(db)
    first = login(db, user.email)
    second = service.refresh(db, first.refresh_token)
    assert second.refresh_token != first.refresh_token
    with pytest.raises(UnauthorizedError) as exc:
        service.refresh(db, first.refresh_token)
    assert exc.value.code == "TOKEN_REUSED"


def test_reusing_revoked_refresh_token_revokes_every_session(db):
    user = make_user(db)
    first = login(db, user.email)
    second = service.refresh(db, first.refresh_token)
    with pytest.raises(UnauthorizedError):
        service.refresh(db, first.refresh_token)  # reuso → suspeita de vazamento
    with pytest.raises(UnauthorizedError):
        service.refresh(db, second.refresh_token)  # a sessão "boa" também caiu


def test_refresh_without_token_or_with_access_token_fails(db):
    user = make_user(db)
    tokens = login(db, user.email)
    with pytest.raises(UnauthorizedError):
        service.refresh(db, None)
    with pytest.raises(UnauthorizedError):
        service.refresh(db, tokens.access_token)


def test_refresh_for_deactivated_user_fails(db):
    user = make_user(db)
    tokens = login(db, user.email)
    user.is_active = False
    db.flush()
    with pytest.raises(UnauthorizedError):
        service.refresh(db, tokens.refresh_token)


def test_logout_revokes_refresh_token_and_is_idempotent(db):
    user = make_user(db)
    tokens = login(db, user.email)
    service.logout(db, tokens.refresh_token)
    service.logout(db, tokens.refresh_token)
    service.logout(db, "lixo")
    service.logout(db, None)
    with pytest.raises(UnauthorizedError):
        service.refresh(db, tokens.refresh_token)


def test_get_me(db):
    user = make_user(db, Role.PROFESSOR)
    me = service.get_me(db, current_user(Role.PROFESSOR, user.id))
    assert me.email == user.email
    with pytest.raises(NotFoundError):
        service.get_me(db, current_user(Role.PROFESSOR, 123456789))


def test_change_password_requires_current_and_revokes_sessions(db):
    user = make_user(db)
    tokens = login(db, user.email)
    actor = current_user(Role.RESPONSAVEL, user.id)
    with pytest.raises(BusinessRuleError):
        service.change_password(
            db, actor, PasswordChange(current_password="errada", new_password="NovaSenha9")
        )
    service.change_password(
        db, actor, PasswordChange(current_password=DEFAULT_PASSWORD, new_password="NovaSenha9")
    )
    login(db, user.email, "NovaSenha9")
    with pytest.raises(UnauthorizedError):
        service.refresh(db, tokens.refresh_token)


def test_create_user_and_duplicate_email(db):
    data = UserCreate(
        email="Nova@Escola.com", nome="Nova Pessoa", password="Senha1234", role=Role.FINANCEIRO
    )
    created = service.create_user(db, data)
    assert created.email == "nova@escola.com"
    assert created.role == Role.FINANCEIRO
    stored = db.get(User, created.id)
    assert stored is not None
    assert stored.password_hash != "Senha1234"
    with pytest.raises(ConflictError):
        service.create_user(db, data)


def test_update_user_deactivation_revokes_sessions(db):
    admin = make_user(db, Role.ADMIN)
    target = make_user(db, Role.SECRETARIA)
    tokens = login(db, target.email)
    updated = service.update_user(
        db,
        target.id,
        UserUpdate(is_active=False, nome="Sec Antiga"),
        current_user(Role.ADMIN, admin.id),
    )
    assert updated.is_active is False
    assert updated.nome == "Sec Antiga"
    with pytest.raises(UnauthorizedError):
        service.refresh(db, tokens.refresh_token)


def test_admin_cannot_lock_itself_out(db):
    admin = make_user(db, Role.ADMIN)
    actor = current_user(Role.ADMIN, admin.id)
    with pytest.raises(BusinessRuleError):
        service.update_user(db, admin.id, UserUpdate(is_active=False), actor)
    with pytest.raises(BusinessRuleError):
        service.update_user(db, admin.id, UserUpdate(role=Role.PROFESSOR), actor)
    with pytest.raises(NotFoundError):
        service.update_user(db, 987654321, UserUpdate(nome="Fulano"), actor)


def test_list_users_and_get_user_read(db):
    user = make_user(db, Role.PROFESSOR)
    page = service.list_users(db, role=Role.PROFESSOR, limit=50, offset=0)
    assert user.id in [u.id for u in page.items]
    found = service.get_user_read(db, user.id)
    assert found is not None
    assert found.email == user.email
    assert service.get_user_read(db, 987654321) is None
