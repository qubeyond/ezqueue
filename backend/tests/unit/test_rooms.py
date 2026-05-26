from tests.conftest import decode_token


async def test_create_room_success(client, user_headers, mock_redis):
    mock_redis.exists.return_value = 0
    resp = await client.post("/api/v1/rooms", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "room_id" in data
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_create_room_no_auth(client):
    resp = await client.post("/api/v1/rooms")
    assert resp.status_code == 401


async def test_create_room_returns_admin_token(client, user_headers, mock_redis):
    mock_redis.exists.return_value = 0
    resp = await client.post("/api/v1/rooms", headers=user_headers)
    token = resp.json()["access_token"]
    payload = decode_token(token)
    assert payload["role"] == "admin"
    assert payload["room_id"] == resp.json()["room_id"]


async def test_close_room_success(client, admin_headers, mock_redis):
    mock_redis.get.return_value = "test_admin"
    mock_redis.lrange.return_value = ["A"]
    resp = await client.delete("/api/v1/rooms/ROOM01", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


async def test_close_room_requires_admin_role(client, user_headers, mock_redis):
    mock_redis.get.return_value = "test_user"
    resp = await client.delete("/api/v1/rooms/ROOM01", headers=user_headers)
    assert resp.status_code == 403


async def test_close_room_wrong_owner(client, admin_headers, mock_redis):
    mock_redis.get.return_value = "someone_else"
    resp = await client.delete("/api/v1/rooms/ROOM01", headers=admin_headers)
    assert resp.status_code == 403


async def test_close_room_no_auth(client):
    resp = await client.delete("/api/v1/rooms/ROOM01")
    assert resp.status_code == 401


async def test_room_state_closed(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 0
    resp = await client.get("/api/v1/rooms/ROOM01/state", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["room_closed"] is True


async def test_room_state_open(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.hgetall.return_value = {"status": "waiting", "ticket": "", "active_user_id": ""}
    resp = await client.get("/api/v1/rooms/ROOM01/state", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_closed"] is False
    assert data["current_status"] == "waiting"
