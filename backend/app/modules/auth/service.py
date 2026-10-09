"""Casos de uso de autenticação e gestão de usuários."""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, UnauthorizedError
from app.core.roles import Role
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth import repository
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.schemas import (
    LoginRequest,
    PasswordChange,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.shared import clock
from app.shared.pagination import Page

INVALID_CREDENTIALS = "E-mail ou senha inválidos."


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    refresh = create_refresh_token(user.id)
    repository.add_refresh_token(
        db, RefreshToken(user_id=user.id, jti=refresh.jti, expires_at=refresh.expires_at)
    )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role, user.email),
        refresh_token=refresh.token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = repository.get_user_by_email(db, data.email)
    if user is None:
        # Gasta o mesmo tempo de um login real para não revelar quais e-mails existem.
        verify_password(data.password, DUMMY_PASSWORD_HASH)
        raise UnauthorizedError(INVALID_CREDENTIALS, "INVALID_CREDENTIALS")
    if not verify_password(data.password, user.password_hash) or not user.is_active:
        raise UnauthorizedError(INVALID_CREDENTIALS, "INVALID_CREDENTIALS")
    user.last_login_at = clock.now()
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


def refresh(db: Session, refresh_token: str | None) -> TokenResponse:
    """Troca um refresh token válido por um novo par (rotação).

    Se um refresh token JÁ REVOGADO for reapresentado, consideramos que ele vazou: todas
    as sessões do usuário são revogadas.
    """
    if not refresh_token:
        raise UnauthorizedError()
    payload = decode_token(refresh_token, "refresh")
    stored = repository.get_refresh_token_by_jti(db, str(payload.get("jti", "")))
    if stored is None:
        raise UnauthorizedError("Sessão inválida.", "INVALID_TOKEN")
    now = clock.now()
    if stored.revoked_at is not None:
        repository.revoke_all_refresh_tokens(db, stored.user_id, now)
        db.commit()
        raise UnauthorizedError("Sessão inválida. Faça login novamente.", "TOKEN_REUSED")
    user = repository.get_user(db, stored.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Sessão inválida.", "INVALID_TOKEN")
    stored.revoked_at = now
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


def logout(db: Session, refresh_token: str | None) -> None:
    """Revoga o refresh token informado. Idempotente: token inválido não gera erro."""
    if not refresh_token:
        return
    try:
        payload = decode_token(refresh_token, "refresh")
    except UnauthorizedError:
        return
    stored = repository.get_refresh_token_by_jti(db, str(payload.get("jti", "")))
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = clock.now()
        db.commit()


def get_me(db: Session, user: CurrentUser) -> UserRead:
    found = repository.get_user(db, user.id)
    if found is None:
        raise NotFoundError("Usuário não encontrado.")
    return UserRead.model_validate(found)


def change_password(db: Session, user: CurrentUser, data: PasswordChange) -> None:
    found = repository.get_user(db, user.id)
    if found is None or not verify_password(data.current_password, found.password_hash):
        raise BusinessRuleError("Senha atual incorreta.", "SENHA_ATUAL_INCORRETA")
    found.password_hash = hash_password(data.new_password)
    repository.revoke_all_refresh_tokens(db, found.id, clock.now())
    db.commit()


# --- Gestão de usuários (ADMIN) ----------------------------------------------------------


def list_users(db: Session, *, role: Role | None, limit: int, offset: int) -> Page[UserRead]:
    rows, total = repository.list_users(db, role=role, limit=limit, offset=offset)
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in rows], total=total, limit=limit, offset=offset
    )


def create_user(db: Session, data: UserCreate) -> UserRead:
    user = create_user_account(
        db, email=data.email, nome=data.nome, password=data.password, role=data.role
    )
    db.commit()
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, actor: CurrentUser) -> UserRead:
    user = repository.get_user(db, user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado.")
    if user.id == actor.id and (data.is_active is False or data.role not in (None, user.role)):
        raise BusinessRuleError(
            "Você não pode desativar nem trocar o perfil da própria conta.", "AUTO_BLOQUEIO"
        )
    if data.nome is not None:
        user.nome = data.nome
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
        if not data.is_active:
            repository.revoke_all_refresh_tokens(db, user.id, clock.now())
    db.commit()
    return UserRead.model_validate(user)


# --- API pública para outros módulos (não fazem commit) -----------------------------------


def create_user_account(
    db: Session, *, email: str, nome: str, password: str, role: Role
) -> UserRead:
    """Cria uma conta de acesso. Não faz commit: participa da transação de quem chamou."""
    email = email.strip().lower()
    if repository.get_user_by_email(db, email) is not None:
        raise ConflictError("Já existe uma conta com este e-mail.", "EMAIL_JA_CADASTRADO")
    user = repository.add_user(
        db, User(email=email, nome=nome, password_hash=hash_password(password), role=role)
    )
    return UserRead.model_validate(user)


def get_user_read(db: Session, user_id: int) -> UserRead | None:
    user = repository.get_user(db, user_id)
    return UserRead.model_validate(user) if user else None
