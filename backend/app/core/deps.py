"""Dependencies compartilhadas do FastAPI: sessão do banco, usuário autenticado e RBAC.

Uso típico em um router:

    @router.post("/{matricula_id}/aprovar")
    def aprovar(
        matricula_id: int,
        db: DbSession,
        user: CurrentUser = Depends(require_roles(Role.ADMIN, Role.SECRETARIA)),
    ) -> MatriculaRead: ...
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.roles import Role
from app.core.security import decode_token

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False, description="Access token JWT obtido em /auth/login")


@dataclass(frozen=True)
class CurrentUser:
    """Identidade do usuário autenticado, extraída do access token (sem ir ao banco).

    O access token dura poucos minutos; desativar um usuário revoga os refresh tokens,
    então o acesso termina quando o access token atual expirar.
    """

    id: int
    role: Role
    email: str

    @property
    def is_staff(self) -> bool:
        return self.role in (Role.ADMIN, Role.SECRETARIA, Role.FINANCEIRO)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    payload = decode_token(credentials.credentials, "access")
    try:
        return CurrentUser(
            id=int(payload["sub"]), role=Role(payload["role"]), email=payload["email"]
        )
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Token inválido.", "INVALID_TOKEN") from exc


def require_roles(*roles: Role) -> Callable[..., CurrentUser]:
    """Cria uma dependency que só deixa passar usuários com um dos perfis informados."""
    allowed = frozenset(roles)

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise ForbiddenError()
        return user

    dependency.__name__ = f"require_roles_{'_'.join(sorted(r.value for r in allowed))}"
    return dependency


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"
