"""Ponto de entrada da API: monta o app FastAPI com os routers de todos os módulos."""

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core import audit
from app.core.config import settings
from app.core.deps import DbSession
from app.core.exceptions import register_exception_handlers
from app.modules.auth.router import router as auth_router
from app.modules.calendario.router import router as calendario_router
from app.modules.comunicacao.router import router as comunicacao_router
from app.modules.financeiro.router import router as financeiro_router
from app.modules.frequencia.router import router as frequencia_router
from app.modules.matricula.router import router as matricula_router
from app.modules.notas.router import router as notas_router
from app.modules.pessoas.router import router as pessoas_router
from app.modules.turmas.router import router as turmas_router

# Para registrar um módulo novo: importe o router dele e adicione na lista abaixo.
ROUTERS: list[APIRouter] = [
    audit.router,
    auth_router,
    pessoas_router,
    turmas_router,
    matricula_router,
    frequencia_router,
    notas_router,
    financeiro_router,
    calendario_router,
    comunicacao_router,
]


def _register_event_handlers() -> None:
    """Liga os handlers de eventos de domínio entre módulos (ver core/events.py)."""


def create_app() -> FastAPI:
    app = FastAPI(
        title="Semeando API",
        version="0.1.0",
        description="API do sistema de gestão escolar Semeando.",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    register_exception_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    _register_event_handlers()

    @app.get("/api/health", tags=["infra"])
    def health(db: DbSession) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
