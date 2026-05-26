"""
Integration tests for RedisQueueRepo.
Require a running Redis instance at redis://localhost:6379/1.
Run with: pytest tests/integration -m integration
"""

import pytest

pytestmark = pytest.mark.integration

ROOM = "TESTROOM"


async def test_room_not_exists_initially(repo):
    assert not await repo.room_exists(ROOM)


async def test_init_queue_creates_room(repo):
    await repo.init_queue(ROOM, "A")
    assert await repo.room_exists(ROOM)


async def test_get_queues_default(repo):
    await repo.init_queue(ROOM, "A")
    assert await repo.get_queues(ROOM) == ["A"]


async def test_set_and_get_owner(repo):
    await repo.set_owner(ROOM, "fp123")
    assert await repo.get_owner(ROOM) == "fp123"


async def test_take_ticket_increments_counter(repo):
    await repo.init_queue(ROOM, "A")
    code, num = await repo.take_ticket(ROOM, "A", "user1")
    assert code == "A1"
    assert num == 1
    code2, num2 = await repo.take_ticket(ROOM, "A", "user2")
    assert code2 == "A2"
    assert num2 == 2


async def test_get_existing_ticket_returns_position(repo):
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.take_ticket(ROOM, "A", "user2")
    result = await repo.get_existing_ticket(ROOM, "user1")
    assert result is not None
    label, ticket, pos = result
    assert label == "A"
    assert ticket == "A1"
    assert pos == 1


async def test_pick_shortest_queue_avoids_serving(repo):
    await repo.init_queue(ROOM, "A")
    await repo.init_queue(ROOM, "B")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.call_next(ROOM, "A")
    label = await repo.pick_shortest_queue(ROOM)
    assert label == "B"


async def test_call_next_raises_on_empty(repo):
    await repo.init_queue(ROOM, "A")
    with pytest.raises(ValueError, match="empty"):
        await repo.call_next(ROOM, "A")


async def test_call_next_moves_to_serving(repo):
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    served_user, ticket, _ = await repo.call_next(ROOM, "A")
    assert served_user == "user1"
    assert ticket == "A1"


async def test_complete_serving_raises_if_not_serving(repo):
    await repo.init_queue(ROOM, "A")
    with pytest.raises(ValueError, match="not_serving"):
        await repo.complete_serving(ROOM, "A")


async def test_complete_serving_returns_serve_seconds(repo):
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.call_next(ROOM, "A")
    ticket, served_user, _, serve_seconds = await repo.complete_serving(ROOM, "A")
    assert ticket == "A1"
    assert served_user == "user1"
    assert serve_seconds >= 0


async def test_leave_queue_removes_user(repo):
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.leave_queue(ROOM, "user1")
    assert await repo.get_existing_ticket(ROOM, "user1") is None


async def test_add_queue_rebalances(repo):
    await repo.init_queue(ROOM, "A")
    for i in range(4):
        await repo.take_ticket(ROOM, "A", f"user{i}")
    await repo.add_queue(ROOM, "B")
    queues = await repo.get_queues(ROOM)
    assert "B" in queues
    from src.infrastructure.redis.client import queue_list_key

    a_len = await repo._r.llen(queue_list_key(ROOM, "A"))
    b_len = await repo._r.llen(queue_list_key(ROOM, "B"))
    assert b_len == 2
    assert a_len == 2


async def test_remove_queue_redistributes(repo):
    await repo.init_queue(ROOM, "A")
    await repo.init_queue(ROOM, "B")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.take_ticket(ROOM, "B", "user2")
    await repo.take_ticket(ROOM, "B", "user3")
    ok = await repo.remove_queue(ROOM, "B")
    assert ok is True
    from src.infrastructure.redis.client import queue_list_key

    a_len = await repo._r.llen(queue_list_key(ROOM, "A"))
    assert a_len == 3


async def test_remove_last_queue_returns_false(repo):
    await repo.init_queue(ROOM, "A")
    assert await repo.remove_queue(ROOM, "A") is False


async def test_update_avg_serve_exponential_average(repo):
    await repo.update_avg_serve(ROOM, 100)
    from src.infrastructure.redis.client import room_avg_serve_key

    val1 = int(await repo._r.get(room_avg_serve_key(ROOM)))
    assert val1 == 100

    await repo.update_avg_serve(ROOM, 200)
    val2 = int(await repo._r.get(room_avg_serve_key(ROOM)))
    assert val2 == int(0.3 * 200 + 0.7 * 100)


async def test_close_room_keys_cleans_up(repo):
    await repo.set_owner(ROOM, "fp")
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.close_room_keys(ROOM)
    assert not await repo.room_exists(ROOM)
    assert await repo.get_owner(ROOM) is None
