import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    RateLimitError,
    register_exception_handlers,
)


class Body(BaseModel):
    nome: str


@pytest.fixture
def mini_client() -> TestClient:
    mini = FastAPI()
    register_exception_handlers(mini)

    @mini.get("/erro/{tipo}")
    def erro(tipo: str) -> None:
        errors = {
            "404": NotFoundError(),
            "403": ForbiddenError(),
            "409": ConflictError("Já existe.", "DUPLICADO"),
            "fsm": InvalidTransitionError(),
            "422": BusinessRuleError("Regra violada."),
            "429": RateLimitError(),
        }
        if tipo == "500":
            raise RuntimeError("bug")
        raise errors[tipo]

    @mini.post("/body")
    def body(payload: Body) -> Body:
        return payload

    return TestClient(mini, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("tipo", "status", "code"),
    [
        ("404", 404, "NOT_FOUND"),
        ("403", 403, "FORBIDDEN"),
        ("409", 409, "DUPLICADO"),
        ("fsm", 409, "INVALID_TRANSITION"),
        ("422", 422, "BUSINESS_RULE"),
        ("429", 429, "RATE_LIMITED"),
        ("500", 500, "INTERNAL_ERROR"),
    ],
)
def test_errors_use_standard_body(mini_client, tipo, status, code):
    response = mini_client.get(f"/erro/{tipo}")
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"detail", "code"}
    assert body["code"] == code


def test_internal_error_does_not_leak_details(mini_client):
    response = mini_client.get("/erro/500")
    assert "bug" not in response.text


def test_validation_error_has_code_and_field_list(mini_client):
    response = mini_client.post("/body", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["loc"] == ["body", "nome"]


def test_unknown_route_uses_standard_body(mini_client):
    response = mini_client.get("/nao-existe")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
