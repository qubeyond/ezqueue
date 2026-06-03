import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.services.auth import REFRESH_COOKIE
from tests.conftest import decode_token


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_get_token_success(client):
    resp = await client.post("/api/v1/auth/token")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_get_token_sets_refresh_cookie(client):
    resp = await client.post("/api/v1/auth/token")
    assert resp.status_code == 200
    assert REFRESH_COOKIE in resp.cookies


async def test_token_identity_is_server_generated(client):
    # Клиент не передаёт fingerprint — личность выпускает сервер (префикс u_).
    resp = await client.post("/api/v1/auth/token")
    payload = decode_token(resp.json()["access_token"])
    assert payload["sub"].startswith("u_")
    assert payload["role"] == "user"
    assert payload["type"] == "access"


async def test_token_ignores_client_supplied_fingerprint(client):
    # Даже если клиент подсунет ?fingerprint=victim — сервер его игнорирует.
    resp = await client.post("/api/v1/auth/token?fingerprint=victim_id")
    payload = decode_token(resp.json()["access_token"])
    assert payload["sub"] != "victim_id"
    assert payload["sub"].startswith("u_")


async def test_token_reuses_identity_from_refresh_cookie(client):
    # Та же личность сохраняется между запросами через refresh-куку.
    resp = await client.post("/api/v1/auth/token")
    first_sub = decode_token(resp.json()["access_token"])["sub"]
    refresh_cookie = resp.cookies[REFRESH_COOKIE]

    resp2 = await client.post(
        "/api/v1/auth/token",
        cookies={REFRESH_COOKIE: refresh_cookie},
    )
    assert decode_token(resp2.json()["access_token"])["sub"] == first_sub


async def test_refresh_returns_new_access_token(client):
    resp = await client.post("/api/v1/auth/token")
    first_sub = decode_token(resp.json()["access_token"])["sub"]
    refresh_cookie = resp.cookies[REFRESH_COOKIE]

    resp2 = await client.post(
        "/api/v1/auth/refresh",
        cookies={REFRESH_COOKIE: refresh_cookie},
    )
    assert resp2.status_code == 200
    payload = decode_token(resp2.json()["access_token"])
    assert payload["sub"] == first_sub
    assert payload["type"] == "access"


async def test_refresh_without_cookie_returns_401(client):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_refresh_with_access_token_as_refresh_returns_401(client):
    resp = await client.post("/api/v1/auth/token")
    access = resp.json()["access_token"]
    resp2 = await client.post(
        "/api/v1/auth/refresh",
        cookies={REFRESH_COOKIE: access},
    )
    assert resp2.status_code == 401


async def test_logout_clears_cookie(client):
    resp = await client.post("/api/v1/auth/token")
    assert REFRESH_COOKIE in resp.cookies

    resp2 = await client.post("/api/v1/auth/logout")
    assert resp2.status_code == 200


async def test_token_has_jti(client):
    resp = await client.post("/api/v1/auth/token")
    payload = decode_token(resp.json()["access_token"])
    assert payload.get("jti")
