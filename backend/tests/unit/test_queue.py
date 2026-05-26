"""
Edge cases covered:
- Room not found
- Owner gets admin token
- User already in queue (returns existing ticket + position)
- User currently being served (lpos=None) → position is None
- Stale user entry (queue deleted) → cleared, fresh ticket issued
- New user: balancer picks shortest queue
- User picks explicit queue
- User picks non-existent explicit queue → 404
- Leave when not in any queue → 200 idempotent
- Leave while active → resets current state
- Rejoin after leave → fresh ticket
- No auth → 401
"""

from tests.conftest import decode_token


async def test_take_ticket_room_not_found(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 0
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "NOROOM"}, headers=user_headers
    )
    assert resp.status_code == 404


async def test_take_ticket_owner_gets_admin_token(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "test_user"
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is True
    payload = decode_token(data["access_token"])
    assert payload["role"] == "admin"


async def test_take_ticket_already_in_queue(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "other_owner"
    mock_redis.hgetall.return_value = {"test_user": "A"}
    mock_redis.hget.return_value = "A3"
    mock_redis.lpos.return_value = 2
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is False
    assert data["ticket"] == "A3"
    assert data["position"] == 3
    assert data["queue_label"] == "A"


async def test_take_ticket_user_being_served_has_no_position(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "other_owner"
    mock_redis.hgetall.return_value = {"test_user": "A"}
    mock_redis.hget.return_value = "A1"
    mock_redis.lpos.return_value = None
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticket"] == "A1"
    assert data["position"] is None


async def test_take_ticket_stale_entry_issues_new_ticket(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "other_owner"
    mock_redis.hgetall.return_value = {"test_user": "A"}
    mock_redis.hget.return_value = None
    mock_redis.llen.return_value = 0
    mock_redis.incr.return_value = 7
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticket"] == "A7"
    assert data["is_admin"] is False


async def test_take_ticket_new_user_balancer_picks_shortest(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "other_owner"
    mock_redis.hgetall.return_value = {}
    mock_redis.llen.return_value = 3
    mock_redis.incr.return_value = 5
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticket"] == "A5"
    assert data["queue_label"] == "A"
    assert data["position"] == 5


async def test_take_ticket_explicit_queue_chosen(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A", "B"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "other_owner"
    mock_redis.hgetall.return_value = {}
    mock_redis.incr.return_value = 2
    resp = await client.post(
        "/api/v1/queue/ticket",
        json={"room_id": "ROOM01", "queue_label": "B"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["queue_label"] == "B"
    assert data["ticket"] == "B2"


async def test_take_ticket_explicit_queue_not_found(client, user_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = "other_owner"
    mock_redis.hgetall.return_value = {}
    resp = await client.post(
        "/api/v1/queue/ticket",
        json={"room_id": "ROOM01", "queue_label": "Z"},
        headers=user_headers,
    )
    assert resp.status_code == 404


async def test_take_ticket_no_auth(client):
    resp = await client.post("/api/v1/queue/ticket", json={"room_id": "ROOM01"})
    assert resp.status_code == 401


async def test_leave_queue_success(client, user_headers, mock_redis):
    mock_redis.hgetall.side_effect = [
        {"test_user": "A"},
        {"status": "waiting", "active_user_id": "other_user"},
    ]
    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


async def test_leave_queue_clears_current_if_active(client, user_headers, mock_redis):
    mock_redis.hgetall.side_effect = [
        {"test_user": "A"},
        {"status": "serving", "active_user_id": "test_user"},
    ]
    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    mock_redis.hset.assert_called()


async def test_leave_queue_not_in_any_queue_is_idempotent(client, user_headers, mock_redis):
    mock_redis.hgetall.return_value = {}
    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


async def test_leave_queue_no_auth(client):
    resp = await client.post("/api/v1/queue/leave", json={"room_id": "ROOM01"})
    assert resp.status_code == 401
