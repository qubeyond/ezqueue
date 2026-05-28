import logging

from fastapi import HTTPException

from src.domain.repositories import EventPublisher, QueueRepository, TicketRepository
from src.services.auth import AuthService
from src.services.dto import QueueLeft, TicketTaken

logger = logging.getLogger(__name__)


class VisitorService:
    def __init__(
        self,
        queue_repo: QueueRepository,
        ticket_repo: TicketRepository,
        auth_service: AuthService,
        publisher: EventPublisher,
    ) -> None:
        self._qr = queue_repo
        self._tr = ticket_repo
        self._auth = auth_service
        self._pub = publisher

    async def take_ticket(
        self, room_id: str, queue_label_hint: str | None, user_id: str
    ) -> TicketTaken:
        if not await self._qr.room_exists(room_id):
            raise HTTPException(status_code=404, detail="Комната не существует")

        owner = await self._qr.get_owner(room_id)

        if owner == user_id:
            token = self._auth.create_token(user_id, role="admin", room_id=room_id)
            return TicketTaken(is_admin=True, room_id=room_id, access_token=token)

        queues = await self._qr.load_all(room_id)

        for queue in queues:
            if queue.has_user(user_id):
                ticket = queue.find_ticket(user_id)
                pos = queue.position(user_id)

                return TicketTaken(
                    is_admin=False,
                    queue_label=queue.label,
                    ticket=ticket.num if ticket else None,
                    position=pos,
                )

        if queue_label_hint:
            queue = next((q for q in queues if q.label == queue_label_hint), None)
            if queue is None:
                raise HTTPException(status_code=404, detail="Очередь не существует")
        else:
            queue = min(queues, key=lambda q: q.total_length())

        ticket = queue.enqueue(user_id)

        await self._qr.save(queue)
        await self._tr.save(ticket)
        await self._pub.publish(room_id, {"type": "update"})

        logger.info("Ticket %s (queue %s) issued in room %s", ticket.num, queue.label, room_id)

        return TicketTaken(
            is_admin=False,
            queue_label=queue.label,
            ticket=ticket.num,
            position=queue.position(user_id),
        )

    async def leave_queue(self, room_id: str, user_id: str) -> QueueLeft:
        queues = await self._qr.load_all(room_id)

        for queue in queues:
            if queue.has_user(user_id):
                queue.dequeue(user_id)
                await self._qr.save(queue)
                break

        await self._pub.publish(room_id, {"type": "update"})

        return QueueLeft(status="removed")
