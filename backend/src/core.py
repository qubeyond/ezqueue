import os
import json
import time
import secrets
from fastapi import WebSocket
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

ROOM_ID_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_ID_LENGTH = 6


def generate_room_id() -> str:
    return "".join(
        secrets.choice(ROOM_ID_ALPHABET) for _ in range(ROOM_ID_LENGTH)
    )


class RoomConnectionManager:

    def __init__(self):
        self.active_connections: dict[str, set[tuple[WebSocket, str]]] = {}

    async def connect(
        self, room_id: str, websocket: WebSocket, user_id: str | None
    ):
        r_id = room_id.upper().strip()
        safe_user_id = str(user_id) if user_id else "unknown_user"
        if safe_user_id in ["undefined", "null", "None", ""]:
            safe_user_id = "admin_or_unknown"

        await websocket.accept()

        if r_id not in self.active_connections:
            self.active_connections[r_id] = set()

        self.active_connections[r_id].add((websocket, safe_user_id))

    def disconnect(
        self, room_id: str, websocket: WebSocket, user_id: str | None
    ):
        r_id = room_id.upper().strip()

        if r_id in self.active_connections:
            self.active_connections[r_id] = {
                item
                for item in self.active_connections[r_id]
                if item[0] != websocket
            }
            if not self.active_connections[r_id]:
                del self.active_connections[r_id]

    async def broadcast_room_status(self, room_id: str):
        r_id = room_id.upper().strip()
        if r_id not in self.active_connections:
            return

        for websocket, user_id in list(self.active_connections[r_id]):
            try:
                status_data = await get_room_state_data(r_id, user_id)
                payload = json.dumps({"type": "update", "data": status_data})
                await websocket.send_text(payload)
            except Exception:
                self.active_connections[r_id] = {
                    item
                    for item in self.active_connections[r_id]
                    if item[0] != websocket
                }


manager = RoomConnectionManager()


async def get_room_state_data(room_id: str, target_user_id: str = "") -> dict:
    r_id = room_id.upper().strip()
    current_key = f"room:{r_id}:current"

    if not await redis_client.exists(current_key):
        return {
            "room_closed": True,
            "room_id": r_id,
            "client_context": {"should_redirect": True, "message": ""},
            "admin_context": {"should_redirect": True},
        }

    list_key = f"room:{r_id}:list"
    hash_key = f"room:{r_id}:identifiers"

    users_in_q = await redis_client.lrange(list_key, 0, -1)
    tickets = (
        await redis_client.hmget(hash_key, users_in_q) if users_in_q else []
    )

    queue_list = [
        {"user_id": uid, "ticket": t} for uid, t in zip(users_in_q, tickets) if t
    ]
    current_state = await redis_client.hgetall(current_key)

    elapsed_time = 0
    if (
        current_state.get("status") == "serving"
        and "started_at" in current_state
    ):
        try:
            elapsed_time = int(time.time() - float(current_state["started_at"]))
        except ValueError:
            elapsed_time = 0

    my_ticket = "--"
    my_pos = "Нет в очереди"

    current_serving_user = current_state.get("active_user_id", "")
    current_ticket = current_state.get("ticket", "")

    if (
        current_state.get("status") == "serving"
        and current_serving_user == target_user_id
    ):
        my_ticket = f"№ {current_ticket}"
        my_pos = "На приеме"
    else:
        for idx, m in enumerate(queue_list):
            if m["user_id"] == target_user_id:
                my_ticket = f"№ {m['ticket']}"
                my_pos = str(idx + 1)
                break

    should_redirect = (
        current_state.get("status") == "waiting"
        and current_serving_user != target_user_id
        and my_pos == "Нет в очереди"
    )

    return {
        "room_closed": False,
        "room_id": r_id,
        "current_status": current_state.get("status", "waiting"),
        "current_status_label": (
            "Идет прием"
            if current_state.get("status") == "serving"
            else "Ожидание"
        ),
        "elapsed_time": elapsed_time,
        "client_context": {
            "ticket_label": my_ticket,
            "position_label": my_pos,
            "should_redirect": should_redirect,
            "message": "",
        },
        "admin_context": {
            "current_ticket_label": (
                f"№ {current_ticket}" if current_ticket else "ОЖИДАНИЕ"
            ),
            "next_tickets": [f"Талон № {m['ticket']}" for m in queue_list],
        },
    }