"""
Edge cases covered:
- call_next success
- call_next empty queue → 400
- call_next wrong room → 403
- call_next no auth → 401
- call_next user role → 403
- complete success
- complete when not serving → 400
- complete wrong room → 403
- add queue success (next letter assigned automatically)
- add queue rebalances: every 2nd user from longest queue moves to new queue
- add queue when all labels used → 400
- remove queue success
- remove queue redistributes waiting users to shortest remaining queue
- remove last queue → 400
- remove non-existent queue → 400
- stats success
- stats wrong room → 403
- stats no auth → 401
"""


async def test_call_next_success(client, admin_headers, mock_redis, mock_db):
    mock_redis.llen.return_value = 1
    mock_redis.lpop.return_value = "test_user"
    mock_redis.hget.return_value = "A7"
    resp = await client.post(
        "/api/v1/admin/next",
        json={"room_id": "ROOM01", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "called"
    assert data["ticket"] == "A7"
    assert data["queue_label"] == "A"


async def test_call_next_empty_queue(client, admin_headers, mock_redis):
    mock_redis.llen.return_value = 0
    resp = await client.post(
        "/api/v1/admin/next",
        json={"room_id": "ROOM01", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "пуста" in resp.json()["detail"].lower()


async def test_call_next_wrong_room(client, admin_headers):
    resp = await client.post(
        "/api/v1/admin/next",
        json={"room_id": "ROOM99", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 403


async def test_call_next_no_auth(client):
    resp = await client.post("/api/v1/admin/next", json={"room_id": "ROOM01", "queue_label": "A"})
    assert resp.status_code == 401


async def test_call_next_user_role_forbidden(client, user_headers):
    resp = await client.post(
        "/api/v1/admin/next",
        json={"room_id": "ROOM01", "queue_label": "A"},
        headers=user_headers,
    )
    assert resp.status_code == 403


async def test_complete_serving_success(client, admin_headers, mock_redis, mock_db):
    mock_redis.hgetall.return_value = {"status": "serving", "ticket": "A7", "active_user_id": "u1"}
    resp = await client.post(
        "/api/v1/admin/complete",
        json={"room_id": "ROOM01", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_complete_serving_not_active(client, admin_headers, mock_redis):
    mock_redis.hgetall.return_value = {"status": "waiting", "ticket": "", "active_user_id": ""}
    resp = await client.post(
        "/api/v1/admin/complete",
        json={"room_id": "ROOM01", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


async def test_complete_wrong_room(client, admin_headers):
    resp = await client.post(
        "/api/v1/admin/complete",
        json={"room_id": "ROOM99", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 403


async def test_add_queue_success(client, admin_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    mock_redis.llen.return_value = 0
    resp = await client.post(
        "/api/v1/admin/queue/add",
        json={"room_id": "ROOM01"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"
    assert data["queue_label"] == "B"


async def test_add_queue_rebalances_users(client, admin_headers, mock_redis):
    mock_redis.lrange.side_effect = [
        ["A"],
        ["A"],
        ["u1", "u2", "u3", "u4"],
    ]
    mock_redis.llen.return_value = 4
    mock_redis.hmget.return_value = ["A2", "A4"]
    resp = await client.post(
        "/api/v1/admin/queue/add",
        json={"room_id": "ROOM01"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["queue_label"] == "B"
    mock_redis.pipeline.assert_called()


async def test_add_queue_max_reached(client, admin_headers, mock_redis):
    mock_redis.lrange.return_value = list("ABCDEFGHIJ")
    resp = await client.post(
        "/api/v1/admin/queue/add",
        json={"room_id": "ROOM01"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


async def test_remove_queue_success(client, admin_headers, mock_redis):
    mock_redis.lrange.side_effect = [
        ["A", "B"],
        ["A", "B"],
        [],
    ]
    mock_redis.llen.return_value = 0
    resp = await client.request(
        "DELETE",
        "/api/v1/admin/queue/remove",
        json={"room_id": "ROOM01", "queue_label": "B"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


async def test_remove_queue_redistributes_users(client, admin_headers, mock_redis):
    mock_redis.lrange.side_effect = [
        ["A", "B"],
        ["A", "B"],
        ["u1", "u2"],
    ]
    mock_redis.llen.return_value = 1
    mock_redis.hmget.return_value = ["B1", "B2"]
    resp = await client.request(
        "DELETE",
        "/api/v1/admin/queue/remove",
        json={"room_id": "ROOM01", "queue_label": "B"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    mock_redis.pipeline.assert_called()


async def test_remove_last_queue_forbidden(client, admin_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    resp = await client.request(
        "DELETE",
        "/api/v1/admin/queue/remove",
        json={"room_id": "ROOM01", "queue_label": "A"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


async def test_remove_nonexistent_queue(client, admin_headers, mock_redis):
    mock_redis.lrange.return_value = ["A"]
    resp = await client.request(
        "DELETE",
        "/api/v1/admin/queue/remove",
        json={"room_id": "ROOM01", "queue_label": "Z"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


async def test_stats_success(client, admin_headers, mock_db):
    resp = await client.get("/api/v1/admin/stats/ROOM01", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_id"] == "ROOM01"
    assert "total_tickets" in data
    assert "completed" in data


async def test_stats_wrong_room(client, admin_headers):
    resp = await client.get("/api/v1/admin/stats/ROOM99", headers=admin_headers)
    assert resp.status_code == 403


async def test_stats_no_auth(client):
    resp = await client.get("/api/v1/admin/stats/ROOM01")
    assert resp.status_code == 401
