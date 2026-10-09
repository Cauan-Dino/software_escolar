from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.roles import Role
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_store_plain_text_and_verifies():
    hashed = hash_password("Senha@123")
    assert "Senha@123" not in hashed
    assert hashed.startswith("$argon2")
    assert verify_password("Senha@123", hashed)
    assert not verify_password("senha errada", hashed)


def test_verify_password_with_garbage_hash_returns_false():
    assert not verify_password("x", "isto-nao-e-um-hash")


def test_access_token_roundtrip_contains_role_and_type():
    token = create_access_token(7, Role.SECRETARIA, "sec@escola.com")
    payload = decode_token(token, "access")
    assert payload["sub"] == "7"
    assert payload["role"] == "SECRETARIA"
    assert payload["type"] == "access"


def test_refresh_token_cannot_be_used_as_access_token():
    refresh = create_refresh_token(7)
    with pytest.raises(UnauthorizedError):
        decode_token(refresh.token, "access")
    assert decode_token(refresh.token, "refresh")["jti"] == refresh.jti


def test_expired_token_is_rejected_with_specific_code():
    payload = {
        "sub": "1",
        "type": "access",
        "role": "ADMIN",
        "email": "a@a.com",
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    with pytest.raises(UnauthorizedError) as exc:
        decode_token(token, "access")
    assert exc.value.code == "TOKEN_EXPIRED"


def test_token_signed_with_other_key_is_rejected():
    payload = {"sub": "1", "type": "access", "exp": datetime.now(UTC) + timedelta(minutes=5)}
    forged = jwt.encode(payload, "chave-do-atacante-com-32-caracteres!!", algorithm=ALGORITHM)
    with pytest.raises(UnauthorizedError) as exc:
        decode_token(forged, "access")
    assert exc.value.code == "INVALID_TOKEN"


def test_token_with_alg_none_is_rejected():
    payload = {"sub": "1", "type": "access", "exp": datetime.now(UTC) + timedelta(minutes=5)}
    unsigned = jwt.encode(payload, None, algorithm="none")
    with pytest.raises(UnauthorizedError):
        decode_token(unsigned, "access")
