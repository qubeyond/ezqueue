from src.domain.entities import Queue, Ticket
from tests.conftest import decode_token


async def test_take_ticket_room_not_found(client, user_headers, mock_queue_repo):
    mock_queue_repo.room_exists.return_value = False
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "NOROOM"}, headers=user_headers
    )
    assert resp.status_code == 404


async def test_take_ticket_owner_gets_admin_token(client, user_headers, mock_queue_repo):
    mock_queue_repo.room_exists.return_value = True
    mock_queue_repo.get_owner.return_value = "test_user"
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is True
    payload = decode_token(data["access_token"])
    assert payload["role"] == "admin"


async def test_take_ticket_already_in_queue(client, user_headers, mock_queue_repo):
    ticket = Ticket(num="A3", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", waiting=[ticket])
    mock_queue_repo.get_owner.return_value = "other_owner"
    mock_queue_repo.load_all.return_value = [queue]
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is False
    assert data["ticket"] == "A3"
    assert data["position"] == 1
    assert data["queue_label"] == "A"


async def test_take_ticket_user_being_served_has_no_position(client, user_headers, mock_queue_repo):
    ticket = Ticket(num="A1", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", serving=ticket)
    mock_queue_repo.get_owner.return_value = "other_owner"
    mock_queue_repo.load_all.return_value = [queue]
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticket"] == "A1"
    assert data["position"] is None


async def test_take_ticket_new_user_balancer_picks_shortest(client, user_headers, mock_queue_repo):
    queue = Queue(label="A", room_id="ROOM01", waiting=[], ticket_counter=4)
    mock_queue_repo.get_owner.return_value = "other_owner"
    mock_queue_repo.load_all.return_value = [queue]
    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticket"] == "A5"
    assert data["queue_label"] == "A"
    assert data["position"] == 1


async def test_take_ticket_explicit_queue_chosen(client, user_headers, mock_queue_repo):
    mock_queue_repo.get_owner.return_value = "other_owner"
    mock_queue_repo.load_all.return_value = [
        Queue(label="A", room_id="ROOM01", ticket_counter=0),
        Queue(label="B", room_id="ROOM01", ticket_counter=1),
    ]
    resp = await client.post(
        "/api/v1/queue/ticket",
        json={"room_id": "ROOM01", "queue_label": "B"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["queue_label"] == "B"
    assert data["ticket"] == "B2"


async def test_take_ticket_explicit_queue_not_found(client, user_headers, mock_queue_repo):
    mock_queue_repo.get_owner.return_value = "other_owner"
    mock_queue_repo.load_all.return_value = [Queue(label="A", room_id="ROOM01")]
    resp = await client.post(
        "/api/v1/queue/ticket",
        json={"room_id": "ROOM01", "queue_label": "C"},
        headers=user_headers,
    )
    assert resp.status_code == 404


async def test_take_ticket_no_auth(client):
    resp = await client.post("/api/v1/queue/ticket", json={"room_id": "ROOM01"})
    assert resp.status_code == 401


async def test_leave_queue_success(client, user_headers, mock_queue_repo):
    ticket = Ticket(num="A1", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", waiting=[ticket])
    mock_queue_repo.load_all.return_value = [queue]
    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


async def test_leave_queue_clears_serving_if_active(client, user_headers, mock_queue_repo):
    ticket = Ticket(num="A1", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", serving=ticket)
    mock_queue_repo.load_all.return_value = [queue]
    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    saved = mock_queue_repo.save.call_args[0][0]
    assert saved.serving is None


async def test_leave_queue_not_in_any_queue_is_idempotent(client, user_headers, mock_queue_repo):
    mock_queue_repo.load_all.return_value = [Queue(label="A", room_id="ROOM01")]
    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


async def test_leave_queue_no_auth(client):
    resp = await client.post("/api/v1/queue/leave", json={"room_id": "ROOM01"})
    assert resp.status_code == 401
