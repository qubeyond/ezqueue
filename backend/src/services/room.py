import logging

from fastapi import HTTPException

from src.domain.entities import RoomClosed, RoomCreated
from src.domain.repositories import QueueRepo, RoomRepo, WebSocketBroadcaster
from src.infrastructure.redis.client import DEFAULT_QUEUE, generate_room_id
from src.services.auth import AuthService

logger = logging.getLogger(__name__)


class RoomService:
    def __init__(
        self,
        queue_repo: QueueRepo,
        room_repo: RoomRepo,
        auth_service: AuthService,
        broadcaster: WebSocketBroadcaster,
    ) -> None:
        self._qr = queue_repo
        self._rr = room_repo
        self._auth = auth_service
        self._bc = broadcaster

    async def create_room(self, fingerprint: str) -> RoomCreated:
        for _ in range(10):
            room_id = generate_room_id()
            if not await self._qr.room_exists(room_id):
                await self._qr.set_owner(room_id, fingerprint)
                await self._qr.init_queue(room_id, DEFAULT_QUEUE)
                await self._rr.create(room_id, fingerprint)
                token = self._auth.create_token(fingerprint, role="admin", room_id=room_id)
                logger.info("Room %s created by %s", room_id, fingerprint)
                return RoomCreated(room_id=room_id, access_token=token)
        raise HTTPException(status_code=500, detail="Ошибка генерации ID комнаты")

    async def close_room(self, room_id: str, fingerprint: str) -> RoomClosed:
        owner = await self._qr.get_owner(room_id)
        if owner != fingerprint:
            raise HTTPException(status_code=403, detail="Доступ запрещён")
        await self._bc.broadcast(room_id, {"type": "update", "data": {"room_closed": True}})
        await self._qr.close_room_keys(room_id)
        await self._rr.close(room_id)
        logger.info("Room %s closed by %s", room_id, fingerprint)
        return RoomClosed(status="closed")

    async def get_state(self, room_id: str, user_id: str) -> dict:
        return await self._qr.get_state(room_id, user_id)
