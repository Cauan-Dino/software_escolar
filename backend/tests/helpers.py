"""Funções auxiliares dos testes (tokens, usuários fictícios)."""

from app.core.deps import CurrentUser
from app.core.roles import Role
from app.core.security import create_access_token


def auth_headers(user_id: int, role: Role, email: str | None = None) -> dict[str, str]:
    token = create_access_token(user_id, role, email or f"user{user_id}@teste.com")
    return {"Authorization": f"Bearer {token}"}


def current_user(role: Role, user_id: int = 999_001) -> CurrentUser:
    return CurrentUser(id=user_id, role=role, email=f"user{user_id}@teste.com")
