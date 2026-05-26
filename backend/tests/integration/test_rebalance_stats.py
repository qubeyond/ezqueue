"""
Integration tests for the rebalance+stats bug:
when a user is redistributed from queue A to queue B via add_queue,
their ticket's queue_label in Redis changes to "B", but the TicketEvent
row in the DB still has queue_label="A".

mark_called / mark_completed previously filtered by queue_label, so the
UPDATE matched 0 rows — the ticket was never recorded as called/completed
in the stats.

These tests use a real Redis (DB #1) and an in-memory SQLite DB.
Run with: pytest tests/integration -m integration
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.db.base import init_db
from src.infrastructure.db.repositories import SQLAlchemyTicketRepo
from src.infrastructure.redis.queue_manager import RedisQueueRepo

pytestmark = pytest.mark.integration

ROOM = "REBTEST"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(engine)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def ticket_repo(db_session: AsyncSession):
    return SQLAlchemyTicketRepo(db_session)


# ── Reproduce the bug ──────────────────────────────────────────────────────────


async def test_mark_called_after_rebalance_updates_db(repo: RedisQueueRepo, ticket_repo):
    """
    Ticket issued in queue A, user redistributed to B via add_queue.
    mark_called with label="B" must still update the DB row (which has label="A").
    """
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.take_ticket(ROOM, "A", "user2")

    await ticket_repo.create_event(ROOM, "A", "A1", "user1")
    await ticket_repo.create_event(ROOM, "A", "A2", "user2")

    await repo.add_queue(ROOM, "B")

    existing1 = await repo.get_existing_ticket(ROOM, "user1")
    existing2 = await repo.get_existing_ticket(ROOM, "user2")
    assert existing1 is not None
    assert existing2 is not None

    label1, ticket1, _ = existing1
    label2, ticket2, _ = existing2

    served_user, called_ticket, _ = await repo.call_next(ROOM, label1)
    await ticket_repo.mark_called(ROOM, label1, called_ticket)

    events = await ticket_repo.get_events(ROOM)
    called = [e for e in events if e.ticket_num == called_ticket]
    assert len(called) == 1
    assert called[0].called_at is not None, (
        f"called_at is None for ticket {called_ticket} after mark_called with label={label1!r} "
        f"(was originally created with label='A')"
    )


async def test_mark_completed_after_rebalance_updates_db(repo: RedisQueueRepo, ticket_repo):
    """
    Full cycle: issue → rebalance → call_next → complete_serving.
    Both called_at and completed_at must be set for the redistributed ticket.
    """
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.take_ticket(ROOM, "A", "user2")

    await ticket_repo.create_event(ROOM, "A", "A1", "user1")
    await ticket_repo.create_event(ROOM, "A", "A2", "user2")

    await repo.add_queue(ROOM, "B")

    existing = await repo.get_existing_ticket(ROOM, "user2")
    assert existing is not None
    label2, ticket2, _ = existing

    _, called_ticket, _ = await repo.call_next(ROOM, label2)
    await ticket_repo.mark_called(ROOM, label2, called_ticket)

    _, _, _, _ = await repo.complete_serving(ROOM, label2)
    await ticket_repo.mark_completed(ROOM, label2, called_ticket)

    events = await ticket_repo.get_events(ROOM)
    completed = [e for e in events if e.ticket_num == called_ticket]
    assert len(completed) == 1
    assert completed[0].called_at is not None, "called_at not set after rebalance"
    assert completed[0].completed_at is not None, "completed_at not set after rebalance"
    assert completed[0].serve_seconds is not None
    assert completed[0].serve_seconds >= 0


async def test_stats_counts_rebalanced_ticket_as_completed(repo: RedisQueueRepo, ticket_repo):
    """
    get_stats (via get_events) must count the redistributed ticket in 'completed'.
    """
    await repo.init_queue(ROOM, "A")
    for i in range(1, 5):
        await repo.take_ticket(ROOM, "A", f"user{i}")
        await ticket_repo.create_event(ROOM, "A", f"A{i}", f"user{i}")

    await repo.add_queue(ROOM, "B")

    for label in ["A", "B"]:
        served_user, ticket, _ = await repo.call_next(ROOM, label)
        await ticket_repo.mark_called(ROOM, label, ticket)
        await repo.complete_serving(ROOM, label)
        await ticket_repo.mark_completed(ROOM, label, ticket)

    events = await ticket_repo.get_events(ROOM)
    completed = [e for e in events if e.completed_at is not None]
    assert len(completed) == 2, (
        f"Expected 2 completed tickets (1 from A, 1 from B after rebalance), got {len(completed)}"
    )


async def test_non_rebalanced_ticket_unaffected(repo: RedisQueueRepo, ticket_repo):
    """
    Tickets that were NOT redistributed still work correctly after add_queue.
    """
    await repo.init_queue(ROOM, "A")
    await repo.take_ticket(ROOM, "A", "user1")
    await repo.take_ticket(ROOM, "A", "user2")
    await ticket_repo.create_event(ROOM, "A", "A1", "user1")
    await ticket_repo.create_event(ROOM, "A", "A2", "user2")

    await repo.add_queue(ROOM, "B")

    existing1 = await repo.get_existing_ticket(ROOM, "user1")
    assert existing1 is not None
    label1, ticket1, _ = existing1
    assert label1 == "A", "user1 should stay in A (only every 2nd user is moved)"

    _, called_ticket, _ = await repo.call_next(ROOM, "A")
    await ticket_repo.mark_called(ROOM, "A", called_ticket)
    await repo.complete_serving(ROOM, "A")
    await ticket_repo.mark_completed(ROOM, "A", called_ticket)

    events = await ticket_repo.get_events(ROOM)
    row = next(e for e in events if e.ticket_num == called_ticket)
    assert row.called_at is not None
    assert row.completed_at is not None
