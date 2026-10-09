import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.deps import CurrentUser, get_current_user, require_roles
from app.core.exceptions import register_exception_handlers
from app.core.roles import Role
from app.core.security import create_refresh_token
from tests.helpers import auth_headers


@pytest.fixture
def mini_client() -> TestClient:
    mini = FastAPI()
    register_exception_handlers(mini)

    @mini.get("/me")
    def me(user: CurrentUser = Depends(get_current_user)) -> dict[str, object]:
        return {"id": user.id, "role": user.role, "staff": user.is_staff}

    @mini.get("/so-admin")
    def so_admin(user: CurrentUser = Depends(require_roles(Role.ADMIN))) -> dict[str, int]:
        return {"id": user.id}

    return TestClient(mini)


def test_missing_token_returns_401_with_standard_body(mini_client):
    response = mini_client.get("/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado.", "code": "UNAUTHORIZED"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_garbage_token_returns_401(mini_client):
    response = mini_client.get("/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_refresh_token_is_not_accepted_as_bearer(mini_client):
    refresh = create_refresh_token(1).token
    response = mini_client.get("/me", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 401


def test_valid_token_returns_current_user(mini_client):
    response = mini_client.get("/me", headers=auth_headers(10, Role.FINANCEIRO))
    assert response.status_code == 200
    assert response.json() == {"id": 10, "role": "FINANCEIRO", "staff": True}


def test_require_roles_blocks_other_roles_with_403(mini_client):
    response = mini_client.get("/so-admin", headers=auth_headers(10, Role.RESPONSAVEL))
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_require_roles_allows_listed_role(mini_client):
    response = mini_client.get("/so-admin", headers=auth_headers(3, Role.ADMIN))
    assert response.status_code == 200
