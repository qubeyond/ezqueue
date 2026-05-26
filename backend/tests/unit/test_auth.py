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
    resp = await client.post("/api/v1/auth/token?fingerprint=abc12345")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_get_token_sets_refresh_cookie(client):
    resp = await client.post("/api/v1/auth/token?fingerprint=abc12345")
    assert resp.status_code == 200
    assert REFRESH_COOKIE in resp.cookies


async def test_get_token_short_fingerprint(client):
    resp = await client.post("/api/v1/auth/token?fingerprint=short")
    assert resp.status_code == 422


async def test_get_token_missing_fingerprint(client):
    resp = await client.post("/api/v1/auth/token")
    assert resp.status_code == 422


async def test_token_is_valid_jwt(client):
    resp = await client.post("/api/v1/auth/token?fingerprint=myfingerprint123")
    token = resp.json()["access_token"]
    payload = decode_token(token)
    assert payload["sub"] == "myfingerprint123"
    assert payload["role"] == "user"
    assert payload["type"] == "access"


async def test_refresh_returns_new_access_token(client):
    resp = await client.post("/api/v1/auth/token?fingerprint=refresh_user_fp")
    assert resp.status_code == 200
    refresh_cookie = resp.cookies[REFRESH_COOKIE]

    resp2 = await client.post(
        "/api/v1/auth/refresh",
        cookies={REFRESH_COOKIE: refresh_cookie},
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert "access_token" in data
    payload = decode_token(data["access_token"])
    assert payload["sub"] == "refresh_user_fp"
    assert payload["type"] == "access"


async def test_refresh_without_cookie_returns_401(client):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_refresh_with_access_token_as_refresh_returns_401(client):
    resp = await client.post("/api/v1/auth/token?fingerprint=abc12345")
    access = resp.json()["access_token"]
    resp2 = await client.post(
        "/api/v1/auth/refresh",
        cookies={REFRESH_COOKIE: access},
    )
    assert resp2.status_code == 401


async def test_logout_clears_cookie(client):
    resp = await client.post("/api/v1/auth/token?fingerprint=logout_user_fp")
    assert REFRESH_COOKIE in resp.cookies

    resp2 = await client.post("/api/v1/auth/logout")
    assert resp2.status_code == 200
