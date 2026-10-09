from app.core.config import settings
from app.core.roles import Role
from tests.factories import DEFAULT_PASSWORD, headers_of, make_user

LOGIN = "/api/v1/auth/login"


def do_login(client, email, password=DEFAULT_PASSWORD):
    return client.post(LOGIN, json={"email": email, "password": password})


def test_login_happy_path_sets_httponly_cookie(client, db):
    user = make_user(db, Role.SECRETARIA)
    response = do_login(client, user.email)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "SECRETARIA"
    assert "password_hash" not in body["user"]
    cookie = response.headers["set-cookie"]
    assert settings.refresh_cookie_name in cookie
    assert "HttpOnly" in cookie
    assert "samesite=strict" in cookie.lower()


def test_login_wrong_password_returns_401(client, db):
    user = make_user(db)
    response = do_login(client, user.email, "errada123")
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_login_invalid_payload_returns_422(client):
    assert client.post(LOGIN, json={"email": "nao-e-email"}).status_code == 422


def test_login_is_rate_limited(client, db):
    user = make_user(db)
    for _ in range(settings.login_rate_limit_per_minute):
        do_login(client, user.email, "errada123")
    response = do_login(client, user.email)
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"


def test_refresh_via_cookie_and_via_body(client, db):
    user = make_user(db)
    login_response = do_login(client, user.email)
    via_cookie = client.post("/api/v1/auth/refresh")  # o TestClient reenvia o cookie
    assert via_cookie.status_code == 200
    via_body = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": via_cookie.json()["refresh_token"]}
    )
    assert via_body.status_code == 200
    old = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login_response.json()["refresh_token"]}
    )
    assert old.status_code == 401


def test_logout_clears_cookie_and_revokes(client, db):
    user = make_user(db)
    do_login(client, user.email)
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    client.cookies.clear()
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_me_requires_token(client, db):
    assert client.get("/api/v1/auth/me").status_code == 401
    user = make_user(db, Role.PROFESSOR)
    response = client.get("/api/v1/auth/me", headers=headers_of(user))
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_change_password(client, db):
    user = make_user(db)
    response = client.post(
        "/api/v1/auth/me/senha",
        json={"current_password": DEFAULT_PASSWORD, "new_password": "OutraSenha1"},
        headers=headers_of(user),
    )
    assert response.status_code == 204
    assert do_login(client, user.email, "OutraSenha1").status_code == 200


def test_change_password_rejects_weak_password(client, db):
    user = make_user(db)
    response = client.post(
        "/api/v1/auth/me/senha",
        json={"current_password": DEFAULT_PASSWORD, "new_password": "fraca"},
        headers=headers_of(user),
    )
    assert response.status_code == 422


def test_user_management_is_admin_only(client, db, headers_for):
    payload = {"email": "x@escola.com", "nome": "Fulano", "password": "Senha1234", "role": "ADMIN"}
    assert client.post("/api/v1/auth/users", json=payload).status_code == 401
    for role in (Role.SECRETARIA, Role.FINANCEIRO, Role.PROFESSOR, Role.RESPONSAVEL):
        response = client.post("/api/v1/auth/users", json=payload, headers=headers_for(role))
        assert response.status_code == 403, role
    assert client.get("/api/v1/auth/users", headers=headers_for(Role.SECRETARIA)).status_code == 403


def test_admin_creates_lists_and_updates_users(client, db):
    admin = make_user(db, Role.ADMIN)
    headers = headers_of(admin)
    created = client.post(
        "/api/v1/auth/users",
        json={
            "email": "fin@escola.com",
            "nome": "Financeiro",
            "password": "Senha1234",
            "role": "FINANCEIRO",
        },
        headers=headers,
    )
    assert created.status_code == 201
    user_id = created.json()["id"]
    listed = client.get("/api/v1/auth/users", params={"role": "FINANCEIRO"}, headers=headers)
    assert user_id in [u["id"] for u in listed.json()["items"]]
    updated = client.patch(
        f"/api/v1/auth/users/{user_id}", json={"is_active": False}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False
    assert do_login(client, "fin@escola.com", "Senha1234").status_code == 401


def test_update_user_rejects_unknown_fields(client, db):
    admin = make_user(db, Role.ADMIN)
    target = make_user(db)
    response = client.patch(
        f"/api/v1/auth/users/{target.id}",
        json={"password_hash": "x"},
        headers=headers_of(admin),
    )
    assert response.status_code == 422
