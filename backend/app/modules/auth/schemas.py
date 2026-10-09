import re
from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field

from app.core.roles import Role
from app.shared.schemas import InputSchema, OutputSchema


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("A senha precisa ter pelo menos 8 caracteres")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("A senha precisa ter letras e números")
    return value


Password = Annotated[str, Field(max_length=128), AfterValidator(_validate_password)]
"""Senha nova: mínimo 8 caracteres, com letras e números."""


def _normalize_email(value: str) -> str:
    return value.strip().lower()


Email = Annotated[EmailStr, AfterValidator(_normalize_email)]


class LoginRequest(InputSchema):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(InputSchema):
    """O refresh token pode vir no corpo (apps) ou no cookie httpOnly (navegador)."""

    refresh_token: str | None = None


class UserRead(OutputSchema):
    id: int
    email: str
    nome: str
    role: Role
    is_active: bool


class TokenResponse(OutputSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    user: UserRead


class UserCreate(InputSchema):
    """Criação de usuário pelo ADMIN (único caso em que `role` vem da requisição)."""

    email: Email
    nome: str = Field(min_length=3, max_length=150)
    password: Password
    role: Role


class UserUpdate(InputSchema):
    nome: str | None = Field(default=None, min_length=3, max_length=150)
    role: Role | None = None
    is_active: bool | None = None


class PasswordChange(InputSchema):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password
