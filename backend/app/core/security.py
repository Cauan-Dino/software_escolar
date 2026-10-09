"""Hash de senhas (Argon2) e emissão/validação de tokens JWT."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.roles import Role

ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# Hash usado para gastar o mesmo tempo quando o e-mail não existe (evita enumeração por timing).
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


@dataclass(frozen=True)
class RefreshTokenData:
    token: str
    jti: str
    expires_at: datetime


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: int, role: Role, email: str) -> str:
    now = _now()
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> RefreshTokenData:
    now = _now()
    jti = secrets.token_urlsafe(24)
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "type": "refresh", "jti": jti, "iat": now, "exp": expires_at}
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return RefreshTokenData(token=token, jti=jti, expires_at=expires_at)


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Valida assinatura, expiração e tipo do token. Levanta UnauthorizedError se inválido."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Sessão expirada.", "TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Token inválido.", "INVALID_TOKEN") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Token inválido.", "INVALID_TOKEN")
    return payload
