from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Request, Response, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, get_client_ip, get_current_user, require_roles
from app.core.rate_limit import RateLimiter
from app.core.roles import Role
from app.modules.auth import permissions, service
from app.modules.auth.schemas import (
    LoginRequest,
    PasswordChange,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.shared.pagination import Page, Pagination

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_PATH = "/api/v1/auth"
login_limiter = RateLimiter("login", settings.login_rate_limit_per_minute)


def _login_rate_limit(request: Request) -> None:
    login_limiter.hit(get_client_ip(request))


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="strict",
        path=COOKIE_PATH,
    )


RefreshCookie = Annotated[str | None, Cookie(alias=settings.refresh_cookie_name)]


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(_login_rate_limit)])
def login(payload: LoginRequest, response: Response, db: DbSession) -> TokenResponse:
    tokens = service.login(db, payload)
    _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    db: DbSession,
    cookie_token: RefreshCookie = None,
    payload: RefreshRequest | None = None,
) -> TokenResponse:
    token = (payload.refresh_token if payload else None) or cookie_token
    tokens = service.refresh(db, token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DbSession,
    cookie_token: RefreshCookie = None,
    payload: RefreshRequest | None = None,
) -> None:
    service.logout(db, (payload.refresh_token if payload else None) or cookie_token)
    response.delete_cookie(settings.refresh_cookie_name, path=COOKIE_PATH)


@router.get("/me", response_model=UserRead)
def me(db: DbSession, user: CurrentUser = Depends(get_current_user)) -> UserRead:
    return service.get_me(db, user)


@router.post("/me/senha", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange, db: DbSession, user: CurrentUser = Depends(get_current_user)
) -> None:
    service.change_password(db, user, payload)


@router.get("/users", response_model=Page[UserRead])
def list_users(
    db: DbSession,
    page: Pagination,
    role: Annotated[Role | None, Query()] = None,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_USERS)),
) -> Page[UserRead]:
    return service.list_users(db, role=role, limit=page.limit, offset=page.offset)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: DbSession,
    _: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_USERS)),
) -> UserRead:
    return service.create_user(db, payload)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: DbSession,
    actor: CurrentUser = Depends(require_roles(*permissions.CAN_MANAGE_USERS)),
) -> UserRead:
    return service.update_user(db, user_id, payload, actor)
