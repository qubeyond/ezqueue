import asyncio
import json

import redis.asyncio as aioredis
from fastapi import WebSocket


class RoomConnectionManager:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis
        self._connections: dict[str, set[tuple[WebSocket, str]]] = {}

    async def connect(self, room_id: str, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(room_id, set()).add((websocket, user_id))
        asyncio.create_task(self._listen_pubsub(room_id, websocket))

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        if room_id in self._connections:
            self._connections[room_id] = {
                item for item in self._connections[room_id] if item[0] != websocket
            }

            if not self._connections[room_id]:
                del self._connections[room_id]

    async def _listen_pubsub(self, room_id: str, websocket: WebSocket) -> None:
        pubsub = self._r.pubsub()
        await pubsub.subscribe(f"room:{room_id}:updates")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])
        except Exception:
            pass
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()

    async def publish(self, room_id: str, payload: dict) -> None:
        await self._r.publish(f"room:{room_id}:updates", json.dumps(payload))
