import json
import logging
import re
from typing import Annotated

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.domain.repositories import EventPublisher, QueueRepository
from src.infrastructure.redis.connection_manager import MAX_CONNECTIONS_PER_USER
from src.services.auth import AuthService
from src.services.room import RoomService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])

_ROOM_ID_RE = re.compile(r"^[A-Z0-9]{4,12}$")

# Коды закрытия WS (4xxx — кастомные для приложения).
_WS_BAD_TOKEN = 4401
_WS_FORBIDDEN = 4403
_WS_BAD_ROOM = 4400
_WS_TOO_MANY = 4429


@router.websocket("/ws/room/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Annotated[str | None, Query()] = None,
):
    room_id = room_id.upper().strip()

    # Валидация формата ID комнаты (а не любая строка из пути).
    if not _ROOM_ID_RE.match(room_id):
        await websocket.close(code=_WS_BAD_ROOM, reason="Bad room id")
        return

    if not token:
        await websocket.close(code=_WS_BAD_TOKEN, reason="Missing token")
        return

    app_container = websocket.app.state.dishka_container

    auth_service: AuthService = await app_container.get(AuthService)

    try:
        payload = auth_service.decode_token(token)
    except Exception:
        await websocket.close(code=_WS_BAD_TOKEN, reason="Invalid token")
        return

    if payload.get("type") != "access":
        await websocket.close(code=_WS_BAD_TOKEN, reason="Invalid token type")
        return

    user_id: str = payload.get("sub", "unknown")

    async with app_container() as request_container:
        room_service: RoomService = await request_container.get(RoomService)
        publisher: EventPublisher = await request_container.get(EventPublisher)
        queue_repo: QueueRepository = await request_container.get(QueueRepository)

        # Отозванный (logout) токен не пускаем по WS.
        jti = payload.get("jti")
        if jti and await queue_repo.is_token_revoked(jti):
            await websocket.close(code=_WS_BAD_TOKEN, reason="Token revoked")
            return

        # Только участник комнаты (есть талон) или админ.
        if not await room_service.can_access(room_id, user_id):
            await websocket.close(code=_WS_FORBIDDEN, reason="No access to room")
            return

        # Анти-DoS: ограничиваем число одновременных подключений на пользователя.
        if publisher.user_connection_count(user_id) >= MAX_CONNECTIONS_PER_USER:
            await websocket.close(code=_WS_TOO_MANY, reason="Too many connections")
            return

        await publisher.connect(room_id, websocket, user_id)

        try:
            state = await room_service.get_state(room_id, user_id)
            await websocket.send_text(json.dumps({"type": "welcome", "data": state}))

            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error("WS error: %s", e)
        finally:
            # Гарантированно снимаем подписку и отменяем pubsub-таск,
            # даже если соединение упало неожиданно.
            publisher.disconnect(room_id, websocket)
