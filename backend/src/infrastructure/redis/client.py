import secrets

import redis.asyncio as aioredis

ROOM_ID_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_ID_LENGTH = 6
DEFAULT_QUEUE = "A"


def generate_room_id() -> str:
    return "".join(secrets.choice(ROOM_ID_ALPHABET) for _ in range(ROOM_ID_LENGTH))


def queue_list_key(room_id: str, label: str) -> str:
    return f"room:{room_id}:queue:{label}:list"


def queue_hash_key(room_id: str, label: str) -> str:
    return f"room:{room_id}:queue:{label}:identifiers"


def queue_current_key(room_id: str, label: str) -> str:
    return f"room:{room_id}:queue:{label}:current"


def queue_counter_key(room_id: str, label: str) -> str:
    return f"room:{room_id}:queue:{label}:counter"


def room_queues_key(room_id: str) -> str:
    return f"room:{room_id}:queues"


def room_owner_key(room_id: str) -> str:
    return f"room:{room_id}:owner"


def user_queue_key(room_id: str) -> str:
    return f"room:{room_id}:user_queue"


def room_avg_serve_key(room_id: str) -> str:
    return f"room:{room_id}:avg_serve"


def room_serve_count_key(room_id: str) -> str:
    return f"room:{room_id}:serve_count"


async def create_redis_client(url: str) -> aioredis.Redis:
    return aioredis.from_url(url, decode_responses=True)
