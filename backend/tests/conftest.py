"""Fixtures globais dos testes.

- O schema do banco de teste é recriado UMA vez por sessão aplicando as migrations do
  Alembic (assim os testes também validam as migrations).
- Cada teste roda dentro de uma transação que sofre rollback no final: os `commit()` dos
  services viram SAVEPOINTs e nada vaza de um teste para outro.
"""

import os
from collections.abc import Callable, Iterator
from pathlib import Path

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://semeando:semeando@localhost:5433/semeando_test"
)
# Precisa acontecer antes de qualquer import de `app`, para nada apontar para o banco de dev.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "test"
os.environ.pop("DEEPSEEK_API_KEY", None)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.rate_limit import RateLimiter  # noqa: E402
from app.core.roles import Role  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.helpers import auth_headers  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def reset_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    cfg = alembic_config()
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    eng = create_engine(TEST_DATABASE_URL)
    reset_schema(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def app(db: Session) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> Iterator[None]:
    RateLimiter.reset_all()
    yield
    RateLimiter.reset_all()


@pytest.fixture
def headers_for() -> Callable[..., dict[str, str]]:
    """`headers_for(Role.ADMIN)` → header Authorization com um token válido daquele perfil."""

    def _make(role: Role, user_id: int = 999_001, email: str | None = None) -> dict[str, str]:
        return auth_headers(user_id, role, email)

    return _make
