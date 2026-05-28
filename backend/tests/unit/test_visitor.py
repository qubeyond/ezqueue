from src.domain.entities import Queue, Ticket
from tests.conftest import decode_token

# ---------------------------------------------------------------------------
# take_ticket — balancer picks shortest queue
# ---------------------------------------------------------------------------


async def test_take_ticket_balancer_picks_shorter_of_two(client, user_headers, mock_queue_repo):
    long_q = Queue(
        label="A",
        room_id="ROOM01",
        waiting=[
            Ticket(num="A1", user_id="x1", queue_label="A", room_id="ROOM01"),
            Ticket(num="A2", user_id="x2", queue_label="A", room_id="ROOM01"),
        ],
    )
    short_q = Queue(label="B", room_id="ROOM01", waiting=[])
    mock_queue_repo.get_owner.return_value = "other"
    mock_queue_repo.load_all.return_value = [long_q, short_q]

    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    assert resp.json()["queue_label"] == "B"


async def test_take_ticket_balancer_uses_total_length_including_serving(
    client, user_headers, mock_queue_repo
):
    serving = Ticket(num="A1", user_id="x1", queue_label="A", room_id="ROOM01")
    q_a = Queue(label="A", room_id="ROOM01", serving=serving, waiting=[])
    q_b = Queue(
        label="B",
        room_id="ROOM01",
        waiting=[
            Ticket(num="B1", user_id="x2", queue_label="B", room_id="ROOM01"),
            Ticket(num="B2", user_id="x3", queue_label="B", room_id="ROOM01"),
        ],
    )
    mock_queue_repo.get_owner.return_value = "other"
    mock_queue_repo.load_all.return_value = [q_a, q_b]

    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    assert resp.json()["queue_label"] == "A"


# ---------------------------------------------------------------------------
# take_ticket — position correctness
# ---------------------------------------------------------------------------


async def test_take_ticket_position_first_in_empty_queue(client, user_headers, mock_queue_repo):
    mock_queue_repo.get_owner.return_value = "other"
    mock_queue_repo.load_all.return_value = [Queue(label="A", room_id="ROOM01")]

    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    assert resp.json()["position"] == 1


async def test_take_ticket_position_second_behind_one_waiting(
    client, user_headers, mock_queue_repo
):
    existing = Ticket(num="A1", user_id="x1", queue_label="A", room_id="ROOM01")
    mock_queue_repo.get_owner.return_value = "other"
    mock_queue_repo.load_all.return_value = [
        Queue(label="A", room_id="ROOM01", waiting=[existing], ticket_counter=1)
    ]

    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    assert resp.json()["position"] == 2


# ---------------------------------------------------------------------------
# take_ticket — idempotency (already in queue)
# ---------------------------------------------------------------------------


async def test_take_ticket_returns_existing_position_if_already_waiting(
    client, user_headers, mock_queue_repo
):
    ticket = Ticket(num="A3", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", waiting=[ticket])
    mock_queue_repo.get_owner.return_value = "other"
    mock_queue_repo.load_all.return_value = [queue]

    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ticket"] == "A3"
    assert data["position"] == 1
    mock_queue_repo.save.assert_not_called()


async def test_take_ticket_does_not_double_enqueue(client, user_headers, mock_queue_repo):
    ticket = Ticket(num="A1", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", waiting=[ticket])
    mock_queue_repo.get_owner.return_value = "other"
    mock_queue_repo.load_all.return_value = [queue]

    await client.post("/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers)
    await client.post("/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers)

    mock_queue_repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# take_ticket — admin token
# ---------------------------------------------------------------------------


async def test_take_ticket_owner_token_has_room_id_claim(client, user_headers, mock_queue_repo):
    mock_queue_repo.room_exists.return_value = True
    mock_queue_repo.get_owner.return_value = "test_user"

    resp = await client.post(
        "/api/v1/queue/ticket", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    payload = decode_token(resp.json()["access_token"])
    assert payload["room_id"] == "ROOM01"
    assert payload["role"] == "admin"


# ---------------------------------------------------------------------------
# leave_queue
# ---------------------------------------------------------------------------


async def test_leave_queue_removes_correct_user(client, user_headers, mock_queue_repo):
    t1 = Ticket(num="A1", user_id="test_user", queue_label="A", room_id="ROOM01")
    t2 = Ticket(num="A2", user_id="other_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", waiting=[t1, t2])
    mock_queue_repo.load_all.return_value = [queue]

    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    saved_queue: Queue = mock_queue_repo.save.call_args[0][0]
    assert len(saved_queue.waiting) == 1
    assert saved_queue.waiting[0].user_id == "other_user"


async def test_leave_queue_publishes_update(client, user_headers, mock_queue_repo, mock_publisher):
    ticket = Ticket(num="A1", user_id="test_user", queue_label="A", room_id="ROOM01")
    queue = Queue(label="A", room_id="ROOM01", waiting=[ticket])
    mock_queue_repo.load_all.return_value = [queue]

    await client.post("/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers)

    mock_publisher.publish.assert_awaited_once()


async def test_leave_queue_not_in_queue_does_not_save(client, user_headers, mock_queue_repo):
    mock_queue_repo.load_all.return_value = [Queue(label="A", room_id="ROOM01")]

    resp = await client.post(
        "/api/v1/queue/leave", json={"room_id": "ROOM01"}, headers=user_headers
    )

    assert resp.status_code == 200
    mock_queue_repo.save.assert_not_called()
