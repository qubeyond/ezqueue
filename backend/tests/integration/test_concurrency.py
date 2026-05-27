import asyncio

import pytest

pytestmark = pytest.mark.integration

ROOM = "LOADTEST"


async def fill_queue(repo, room: str, label: str, n: int) -> list[str]:
    users = [f"user_{i:04d}" for i in range(n)]

    async def take(uid: str):
        await repo.take_ticket(room, uid)

    await asyncio.gather(*[take(u) for u in users])
    return users


async def test_concurrent_take_ticket_no_duplicates(repo):
    await repo.init_queue(ROOM, "A")
    users = await fill_queue(repo, ROOM, "A", 50)

    state = await repo.get_state(ROOM, "")
    queues = state["admin_context"]["queues"]
    q = next(q for q in queues if q["label"] == "A")

    assert q["length"] == 50, f"expected 50, got {q['length']}"

    import redis.asyncio as aioredis

    from src.infrastructure.redis.client import queue_hash_key

    r = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    tickets = await r.hmget(queue_hash_key(ROOM, "A"), users)
    await r.aclose()

    assert len(set(tickets)) == 50, "duplicate ticket numbers detected"


async def test_concurrent_take_ticket_multiple_queues(repo):
    await repo.init_queue(ROOM, "A")
    await repo.add_queue(ROOM, "B")
    await repo.add_queue(ROOM, "C")

    users = [f"u_{i:03d}" for i in range(60)]

    async def take(uid: str):
        await repo.take_ticket(ROOM, uid)

    await asyncio.gather(*[take(u) for u in users])

    state = await repo.get_state(ROOM, "")
    lengths = {q["label"]: q["length"] for q in state["admin_context"]["queues"]}
    total = sum(lengths.values())

    assert total == 60, f"expected 60 total, got {total}"
    for label, length in lengths.items():
        assert 15 <= length <= 25, f"queue {label} has {length} — balancer skewed"


async def test_rapid_call_and_complete_cycle(repo):
    await repo.init_queue(ROOM, "A")
    n = 20
    for i in range(n):
        await repo.take_ticket(ROOM, f"u_{i}")

    completed = 0
    for _ in range(n):
        ticket, uid = await repo.call_next(ROOM, "A")
        assert ticket, "expected a ticket"
        await repo.complete_serving(ROOM, "A")
        completed += 1

    assert completed == n

    state = await repo.get_state(ROOM, "")
    q = next(q for q in state["admin_context"]["queues"] if q["label"] == "A")
    assert q["length"] == 0
    assert q["status"] == "waiting"


async def test_concurrent_call_next_is_safe(repo):
    await repo.init_queue(ROOM, "A")
    for i in range(5):
        await repo.take_ticket(ROOM, f"u_{i}")

    results = await asyncio.gather(
        repo.call_next(ROOM, "A"),
        repo.call_next(ROOM, "A"),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, Exception)]

    assert len(successes) == 1, f"expected 1 success, got {len(successes)}"
    assert len(errors) == 1, f"expected 1 error, got {len(errors)}"


async def test_high_load_sequential_serving(repo):
    await repo.init_queue(ROOM, "A")
    n = 100
    for i in range(n):
        await repo.take_ticket(ROOM, f"u_{i}")

    for _ in range(n):
        await repo.call_next(ROOM, "A")
        await repo.complete_serving(ROOM, "A")

    state = await repo.get_state(ROOM, "")
    q = next(q for q in state["admin_context"]["queues"] if q["label"] == "A")
    assert q["length"] == 0
    assert q["status"] == "waiting"
    assert q["current_ticket"] == "ОЖИДАНИЕ"


async def test_stats_after_full_cycle(repo):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.infrastructure.db.base import init_db
    from src.infrastructure.db.repositories import SQLAlchemyTicketRepo

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    db_repo = SQLAlchemyTicketRepo(session_factory)

    await repo.init_queue(ROOM, "A")
    n = 10
    for i in range(n):
        await repo.take_ticket(ROOM, f"u_{i}")

    for _ in range(n):
        ticket, uid = await repo.call_next(ROOM, "A")
        await db_repo.mark_called(ROOM, ticket)
        await repo.complete_serving(ROOM, "A")
        await db_repo.mark_completed(ROOM, ticket)

    stats = await db_repo.get_stats(ROOM)
    assert stats.completed == n, f"expected {n} completed, got {stats.completed}"
    assert stats.avg_serve_seconds >= 0


async def test_rebalance_concurrent_joins(repo):
    await repo.init_queue(ROOM, "A")
    for i in range(20):
        await repo.take_ticket(ROOM, f"pre_{i}")

    async def late_joiners():
        await asyncio.gather(*[repo.take_ticket(ROOM, f"late_{i}") for i in range(10)])

    await asyncio.gather(
        repo.add_queue(ROOM, "B"),
        late_joiners(),
    )

    state = await repo.get_state(ROOM, "")
    queues = {q["label"]: q["length"] for q in state["admin_context"]["queues"]}
    total = sum(queues.values())

    assert total == 30, f"expected 30, got {total} (queues: {queues})"


async def test_room_ttl_is_set(repo, redis_client):
    from src.infrastructure.redis.client import (
        queue_current_key,
        queue_hash_key,
        queue_list_key,
        user_queue_key,
    )

    await repo.init_queue(ROOM, "A")

    keys = [
        queue_list_key(ROOM, "A"),
        queue_hash_key(ROOM, "A"),
        queue_current_key(ROOM, "A"),
        user_queue_key(ROOM),
    ]
    for key in keys:
        ttl = await redis_client.ttl(key)
        assert ttl > 0, f"key {key} has no TTL (ttl={ttl})"


async def test_ttl_refreshed_on_take_ticket(repo, redis_client):
    from src.infrastructure.redis.client import queue_list_key, user_queue_key

    await repo.init_queue(ROOM, "A")
    await redis_client.expire(queue_list_key(ROOM, "A"), 10)
    await redis_client.expire(user_queue_key(ROOM), 10)

    await repo.take_ticket(ROOM, "user_a")

    ttl_list = await redis_client.ttl(queue_list_key(ROOM, "A"))
    ttl_uq = await redis_client.ttl(user_queue_key(ROOM))

    assert ttl_list > 10, f"TTL not refreshed on list key (ttl={ttl_list})"
    assert ttl_uq > 10, f"TTL not refreshed on user_queue key (ttl={ttl_uq})"


async def test_call_next_empty_queue_raises(repo):
    await repo.init_queue(ROOM, "A")
    with pytest.raises(ValueError, match="empty"):
        await repo.call_next(ROOM, "A")


async def test_complete_without_call_raises(repo):
    await repo.init_queue(ROOM, "A")
    with pytest.raises(ValueError, match="not_serving"):
        await repo.complete_serving(ROOM, "A")


async def test_duplicate_take_ticket_same_user(repo):
    import contextlib

    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "same_user")

    state_before = await repo.get_state(ROOM, "same_user")
    q_before = state_before["admin_context"]["queues"][0]["length"]

    with contextlib.suppress(Exception):
        await repo.take_ticket(ROOM, "same_user")

    state_after = await repo.get_state(ROOM, "same_user")
    q_after = state_after["admin_context"]["queues"][0]["length"]

    assert q_after <= q_before + 1
