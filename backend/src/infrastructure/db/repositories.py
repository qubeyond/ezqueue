from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Room, Ticket, TicketRecord
from src.infrastructure.db.models import RoomSession, TicketEvent


class SQLAlchemyRoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, room: Room) -> None:
        self._s.add(RoomSession(room_id=room.room_id, admin_fingerprint=room.owner_id))
        await self._s.commit()

    async def load(self, room_id: str) -> Room | None:
        result = await self._s.execute(select(RoomSession).where(RoomSession.room_id == room_id))
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return Room(
            room_id=row.room_id,
            owner_id=row.admin_fingerprint,
            closed=row.closed_at is not None,
        )

    async def close(self, room_id: str) -> None:
        await self._s.execute(
            update(RoomSession)
            .where(RoomSession.room_id == room_id, RoomSession.closed_at.is_(None))
            .values(closed_at=datetime.now(UTC))
        )
        await self._s.commit()


class SQLAlchemyTicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, ticket: Ticket) -> None:
        self._s.add(
            TicketEvent(
                room_id=ticket.room_id,
                queue_label=ticket.queue_label,
                ticket_num=ticket.num,
                user_fingerprint=ticket.user_id,
            )
        )
        await self._s.commit()

    async def mark_called(self, room_id: str, queue_label: str, num: str, at: datetime) -> None:
        await self._s.execute(
            update(TicketEvent)
            .where(
                TicketEvent.room_id == room_id,
                TicketEvent.ticket_num == num,
                TicketEvent.called_at.is_(None),
            )
            .values(called_at=at)
        )
        await self._s.commit()

    async def mark_completed(self, room_id: str, queue_label: str, num: str, at: datetime) -> None:
        await self._s.execute(
            update(TicketEvent)
            .where(
                TicketEvent.room_id == room_id,
                TicketEvent.ticket_num == num,
                TicketEvent.completed_at.is_(None),
            )
            .values(completed_at=at)
        )
        await self._s.commit()

    async def load_history(self, room_id: str) -> list[TicketRecord]:
        result = await self._s.execute(select(TicketEvent).where(TicketEvent.room_id == room_id))
        rows = result.scalars().all()

        return [
            TicketRecord(
                num=r.ticket_num,
                queue_label=r.queue_label,
                joined_at=r.joined_at,
                called_at=r.called_at,
                completed_at=r.completed_at,
            )
            for r in rows
        ]
