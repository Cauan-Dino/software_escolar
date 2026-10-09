def test_health_checks_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_headers_are_present(client):
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_cors_allows_configured_origin_only(client):
    allowed = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    denied = client.options(
        "/api/health",
        headers={"Origin": "https://site-malicioso.com", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in denied.headers


def test_openapi_is_served(client):
    assert client.get("/api/openapi.json").status_code == 200
