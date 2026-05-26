import logging

from fastapi import HTTPException

from src.domain.entities import QueueLeft, TicketTaken
from src.domain.repositories import QueueRepo, RoomRepo, TicketRepo, WebSocketBroadcaster
from src.services.auth import AuthService

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(
        self,
        queue_repo: QueueRepo,
        room_repo: RoomRepo,
        ticket_repo: TicketRepo,
        auth_service: AuthService,
        broadcaster: WebSocketBroadcaster,
    ) -> None:
        self._qr = queue_repo
        self._rr = room_repo
        self._tr = ticket_repo
        self._auth = auth_service
        self._bc = broadcaster

    async def take_ticket(
        self, room_id: str, queue_label_hint: str | None, fingerprint: str
    ) -> TicketTaken:
        if not await self._qr.room_exists(room_id):
            raise HTTPException(status_code=404, detail="Комната не существует")

        owner = await self._qr.get_owner(room_id)
        if owner == fingerprint:
            token = self._auth.create_token(fingerprint, role="admin", room_id=room_id)
            return TicketTaken(is_admin=True, room_id=room_id, access_token=token)

        existing = await self._qr.get_existing_ticket(room_id, fingerprint)
        if existing:
            label, ticket, position = existing
            return TicketTaken(is_admin=False, queue_label=label, ticket=ticket, position=position)

        if queue_label_hint:
            labels = await self._qr.get_queues(room_id)
            if queue_label_hint not in labels:
                raise HTTPException(status_code=404, detail="Очередь не существует")
            label = queue_label_hint
        else:
            label = await self._qr.pick_shortest_queue(room_id)

        ticket_code, num = await self._qr.take_ticket(room_id, label, fingerprint)
        await self._rr.increment_tickets(room_id)
        await self._tr.create_event(room_id, label, ticket_code, fingerprint)
        await self._bc.broadcast(room_id, {"type": "update"})
        logger.info("Ticket %s (queue %s) issued in room %s", ticket_code, label, room_id)
        return TicketTaken(is_admin=False, queue_label=label, ticket=ticket_code, position=num)

    async def leave_queue(self, room_id: str, fingerprint: str) -> QueueLeft:
        await self._qr.leave_queue(room_id, fingerprint)
        await self._bc.broadcast(room_id, {"type": "update"})
        return QueueLeft(status="removed")
