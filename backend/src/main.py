import time
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.html_provider import get_spa_html
from src.core import (
    redis_client,
    manager,
    generate_room_id,
    get_room_state_data,
)

app = FastAPI(title="Room-Based Dumb-UI Queue API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClientJoinRequest(BaseModel):
    room_id: str
    user_identifier: str


class AdminActionRequest(BaseModel):
    room_id: str


@app.get("/", response_class=HTMLResponse)
async def get_spa_interface():
    return get_spa_html()


@app.post("/api/v1/rooms")
async def create_room(admin_id: str = Query(...)):
    for _ in range(10):
        room_id = generate_room_id()
        current_key = f"room:{room_id}:current"
        owner_key = f"room:{room_id}:owner"

        if not await redis_client.exists(current_key):
            await redis_client.set(owner_key, admin_id)
            await redis_client.expire(owner_key, 86400)

            await redis_client.hset(
                current_key,
                mapping={
                    "status": "waiting",
                    "ticket": "",
                    "active_user_id": "",
                    "started_at": "",
                },
            )
            await redis_client.expire(current_key, 86400)

            return {"status": "created", "room_id": room_id}

    raise HTTPException(status_code=500, detail="Ошибка генерации ID комнаты")


@app.post("/api/v1/queue/ticket")
async def take_ticket(payload: ClientJoinRequest):
    room_id = payload.room_id.upper().strip()
    user_id = payload.user_identifier

    current_key = f"room:{room_id}:current"
    owner_key = f"room:{room_id}:owner"

    if not await redis_client.exists(current_key):
        raise HTTPException(status_code=404, detail="Комната не существует")

    room_owner = await redis_client.get(owner_key)
    if room_owner == user_id:
        return {"is_admin": True, "room_id": room_id, "ticket": ""}

    list_key = f"room:{room_id}:list"
    hash_key = f"room:{room_id}:identifiers"
    counter_key = f"room:{room_id}:counter"

    if await redis_client.hexists(hash_key, user_id):
        existing_ticket = await redis_client.hget(hash_key, user_id)
        pos = await redis_client.lpos(list_key, user_id)
        return {
            "status": "already_in_queue",
            "is_admin": False,
            "ticket": existing_ticket,
            "position": (pos + 1) if pos is not None else 1,
        }

    num = await redis_client.incr(counter_key)
    ticket_code = str(num)

    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.hset(hash_key, user_id, ticket_code)
        pipe.rpush(list_key, user_id)
        await pipe.execute()

    await manager.broadcast_room_status(room_id)
    return {"status": "success", "is_admin": False, "ticket": ticket_code}


@app.post("/api/v1/queue/leave")
async def leave_queue(payload: ClientJoinRequest):
    room_id = payload.room_id.upper().strip()
    user_id = payload.user_identifier

    list_key = f"room:{room_id}:list"
    hash_key = f"room:{room_id}:identifiers"
    current_key = f"room:{room_id}:current"

    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.lrem(list_key, 0, user_id)
        pipe.hdel(hash_key, user_id)
        await pipe.execute()

    current_state = await redis_client.hgetall(current_key)
    if current_state.get("active_user_id") == user_id:
        await redis_client.hset(
            current_key,
            mapping={"status": "waiting", "ticket": "", "active_user_id": ""},
        )

    await manager.broadcast_room_status(room_id)
    return {"status": "removed"}


@app.post("/api/v1/admin/terminate")
async def terminate_room(
    payload: AdminActionRequest, admin_id: str = Query(...)
):
    room_id = payload.room_id.upper().strip()
    owner_key = f"room:{room_id}:owner"

    room_owner = await redis_client.get(owner_key)
    if room_owner != admin_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    keys_to_delete = [
        f"room:{room_id}:owner",
        f"room:{room_id}:current",
        f"room:{room_id}:list",
        f"room:{room_id}:identifiers",
        f"room:{room_id}:counter",
    ]

    r_id = room_id.upper().strip()
    if r_id in manager.active_connections:
        for websocket, _ in list(manager.active_connections[r_id]):
            try:
                payload_data = json.dumps(
                    {"type": "update", "data": {"room_closed": True}}
                )
                await websocket.send_text(payload_data)
            except Exception:
                pass

    for key in keys_to_delete:
        await redis_client.delete(key)

    return {"status": "terminated"}


@app.post("/api/v1/admin/next")
async def admin_next(payload: AdminActionRequest):
    room_id = payload.room_id.upper().strip()

    list_key = f"room:{room_id}:list"
    hash_key = f"room:{room_id}:identifiers"
    current_key = f"room:{room_id}:current"

    queue_len = await redis_client.llen(list_key)
    if queue_len == 0:
        raise HTTPException(status_code=400, detail="Очередь комнаты пуста")

    served_user = await redis_client.lpop(list_key)
    ticket = await redis_client.hget(hash_key, served_user)
    await redis_client.hdel(hash_key, served_user)

    await redis_client.hset(
        current_key,
        mapping={
            "status": "serving",
            "ticket": ticket,
            "active_user_id": served_user,
            "started_at": str(time.time()),
        },
    )

    await manager.broadcast_room_status(room_id)
    return {"status": "called", "ticket": ticket}


@app.post("/api/v1/admin/complete")
async def admin_complete(payload: AdminActionRequest):
    room_id = payload.room_id.upper().strip()
    current_key = f"room:{room_id}:current"

    current = await redis_client.hgetall(current_key)
    if current.get("status") != "serving":
        raise HTTPException(status_code=400, detail="Обслуживание не активно")

    await redis_client.hset(
        current_key,
        mapping={"status": "waiting", "ticket": "", "active_user_id": ""},
    )

    await manager.broadcast_room_status(room_id)
    return {"status": "completed"}


@app.websocket("/ws/room/{room_id}")
async def room_websocket_endpoint(
    websocket: WebSocket, room_id: str, user_id: str | None = Query(None)
) -> None:
    normalized_id = room_id.upper().strip()
    u_id = str(user_id) if user_id else "admin"

    await manager.connect(normalized_id, websocket, u_id)

    try:
        initial_state = await get_room_state_data(normalized_id, u_id)
        await websocket.send_text(
            json.dumps({"type": "welcome", "data": initial_state})
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(normalized_id, websocket, u_id)
    except Exception:
        manager.disconnect(normalized_id, websocket, u_id)