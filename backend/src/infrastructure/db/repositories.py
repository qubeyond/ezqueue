from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import TicketEventEntity
from src.infrastructure.db.models import RoomSession, TicketEvent


class SQLAlchemyRoomRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, room_id: str, fingerprint: str) -> None:
        self._s.add(RoomSession(room_id=room_id, admin_fingerprint=fingerprint))
        await self._s.commit()

    async def close(self, room_id: str) -> None:
        await self._s.execute(
            update(RoomSession)
            .where(RoomSession.room_id == room_id, RoomSession.closed_at.is_(None))
            .values(closed_at=datetime.now(UTC))
        )
        await self._s.commit()

    async def increment_tickets(self, room_id: str) -> None:
        await self._s.execute(
            update(RoomSession)
            .where(RoomSession.room_id == room_id, RoomSession.closed_at.is_(None))
            .values(total_tickets=RoomSession.total_tickets + 1)
        )
        await self._s.commit()


class SQLAlchemyTicketRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create_event(
        self, room_id: str, queue_label: str, ticket_num: str, fingerprint: str
    ) -> None:
        self._s.add(
            TicketEvent(
                room_id=room_id,
                queue_label=queue_label,
                ticket_num=ticket_num,
                user_fingerprint=fingerprint,
            )
        )
        await self._s.commit()

    async def mark_called(self, room_id: str, queue_label: str, ticket_num: str) -> None:
        await self._s.execute(
            update(TicketEvent)
            .where(
                TicketEvent.room_id == room_id,
                TicketEvent.ticket_num == ticket_num,
                TicketEvent.called_at.is_(None),
            )
            .values(called_at=datetime.now(UTC))
        )
        await self._s.commit()

    async def mark_completed(self, room_id: str, queue_label: str, ticket_num: str) -> None:
        await self._s.execute(
            update(TicketEvent)
            .where(
                TicketEvent.room_id == room_id,
                TicketEvent.ticket_num == ticket_num,
                TicketEvent.completed_at.is_(None),
            )
            .values(completed_at=datetime.now(UTC))
        )
        await self._s.commit()

    async def get_events(self, room_id: str) -> list[TicketEventEntity]:
        result = await self._s.execute(select(TicketEvent).where(TicketEvent.room_id == room_id))
        rows = result.scalars().all()
        return [
            TicketEventEntity(
                room_id=r.room_id,
                queue_label=r.queue_label,
                ticket_num=r.ticket_num,
                user_fingerprint=r.user_fingerprint,
                joined_at=r.joined_at,
                called_at=r.called_at,
                completed_at=r.completed_at,
            )
            for r in rows
        ]
