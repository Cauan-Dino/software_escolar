"""Exceções da aplicação e o formato padronizado de erro: {"detail": ..., "code": ...}.

Services levantam estas exceções; os handlers registrados em `register_exception_handlers`
as convertem em respostas HTTP. Assim o service não conhece HTTP, só o "tipo" do erro.
"""

import logging
from typing import Any, ClassVar, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: ClassVar[int] = 400
    default_code: ClassVar[str] = "BAD_REQUEST"
    default_detail: ClassVar[str] = "Requisição inválida."

    def __init__(self, detail: str | None = None, code: str | None = None) -> None:
        self.detail = detail or self.default_detail
        self.code = code or self.default_code
        super().__init__(self.detail)


class UnauthorizedError(AppError):
    status_code = 401
    default_code = "UNAUTHORIZED"
    default_detail = "Não autenticado."


class ForbiddenError(AppError):
    status_code = 403
    default_code = "FORBIDDEN"
    default_detail = "Você não tem permissão para esta ação."


class NotFoundError(AppError):
    status_code = 404
    default_code = "NOT_FOUND"
    default_detail = "Recurso não encontrado."


class ConflictError(AppError):
    status_code = 409
    default_code = "CONFLICT"
    default_detail = "A operação conflita com o estado atual do recurso."


class InvalidTransitionError(ConflictError):
    default_code = "INVALID_TRANSITION"
    default_detail = "Transição de status inválida."


class BusinessRuleError(AppError):
    status_code = 422
    default_code = "BUSINESS_RULE"
    default_detail = "A operação viola uma regra de negócio."


class RateLimitError(AppError):
    status_code = 429
    default_code = "RATE_LIMITED"
    default_detail = "Muitas requisições. Tente novamente em instantes."


def error_body(detail: str, code: str, **extra: Any) -> dict[str, Any]:
    return {"detail": detail, "code": code, **extra}


async def _app_error_handler(_: Request, error: Exception) -> JSONResponse:
    exc = cast(AppError, error)
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, UnauthorizedError) else None
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.detail, exc.code), headers=headers
    )


async def _validation_error_handler(_: Request, error: Exception) -> JSONResponse:
    exc = cast(RequestValidationError, error)
    errors = [
        {"loc": list(err.get("loc", [])), "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body("Dados inválidos.", "VALIDATION_ERROR", errors=errors),
    )


async def _http_exception_handler(_: Request, error: Exception) -> JSONResponse:
    exc = cast(StarletteHTTPException, error)
    codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 401: "UNAUTHORIZED", 403: "FORBIDDEN"}
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(str(exc.detail), codes.get(exc.status_code, "HTTP_ERROR")),
        headers=exc.headers,
    )


async def _unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado", exc_info=exc)
    return JSONResponse(
        status_code=500, content=error_body("Erro interno do servidor.", "INTERNAL_ERROR")
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
