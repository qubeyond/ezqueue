import pytest
import redis.asyncio as aioredis

from src.infrastructure.redis.queue_manager import RedisQueueRepo

REDIS_URL = "redis://localhost:6379/1"
QUEUE_TTL = 60
TEST_ROOM = "TESTROOM"


@pytest.fixture
async def redis_client():
    client = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def repo(redis_client):
    return RedisQueueRepo(redis_client, QUEUE_TTL)
