import logging

from fastapi import HTTPException

from src.domain.entities import (
    NextCalled,
    QueueAdded,
    QueueRemoved,
    RoomStats,
    ServingCompleted,
    TicketTimeline,
)
from src.domain.repositories import QueueRepo, TicketRepo, WebSocketBroadcaster

QUEUE_LABELS = list("ABCDEFGHIJ")

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(
        self,
        queue_repo: QueueRepo,
        ticket_repo: TicketRepo,
        broadcaster: WebSocketBroadcaster,
    ) -> None:
        self._qr = queue_repo
        self._tr = ticket_repo
        self._bc = broadcaster

    async def call_next(self, room_id: str, label: str) -> NextCalled:
        try:
            _, ticket, _ = await self._qr.call_next(room_id, label)
        except ValueError:
            raise HTTPException(status_code=400, detail="Очередь пуста") from None
        await self._tr.mark_called(room_id, label, ticket)
        await self._bc.broadcast(room_id, {"type": "update"})
        logger.info("Ticket %s (queue %s) called in room %s", ticket, label, room_id)
        return NextCalled(queue_label=label, ticket=ticket)

    async def complete_serving(self, room_id: str, label: str) -> ServingCompleted:
        try:
            ticket, _, _, serve_seconds = await self._qr.complete_serving(room_id, label)
        except ValueError:
            raise HTTPException(status_code=400, detail="Обслуживание не активно") from None
        await self._tr.mark_completed(room_id, label, ticket)
        if serve_seconds > 0:
            await self._qr.update_avg_serve(room_id, serve_seconds)
        await self._bc.broadcast(room_id, {"type": "update"})
        return ServingCompleted()

    async def add_queue(self, room_id: str) -> QueueAdded:
        existing = await self._qr.get_queues(room_id)
        available = [lbl for lbl in QUEUE_LABELS if lbl not in existing]
        if not available:
            raise HTTPException(status_code=400, detail="Достигнут максимум очередей")
        label = available[0]
        await self._qr.add_queue(room_id, label)
        await self._bc.broadcast(room_id, {"type": "update"})
        return QueueAdded(queue_label=label)

    async def remove_queue(self, room_id: str, label: str) -> QueueRemoved:
        ok = await self._qr.remove_queue(room_id, label)
        if not ok:
            raise HTTPException(
                status_code=400, detail="Нельзя удалить: очередь не найдена или единственная"
            )
        await self._bc.broadcast(room_id, {"type": "update"})
        return QueueRemoved(queue_label=label)

    async def get_stats(self, room_id: str) -> RoomStats:
        events = await self._tr.get_events(room_id)
        completed = [e for e in events if e.completed_at]
        serve_times = [e.serve_seconds for e in completed if e.serve_seconds is not None]
        return RoomStats(
            room_id=room_id,
            total_tickets=len(events),
            completed=len(completed),
            avg_serve_seconds=int(sum(serve_times) / len(serve_times)) if serve_times else 0,
            timeline=[
                TicketTimeline(
                    ticket=e.ticket_num,
                    queue_label=e.queue_label,
                    joined_at=e.joined_at,
                    wait_seconds=e.wait_seconds,
                    serve_seconds=e.serve_seconds,
                )
                for e in events
            ],
        )
