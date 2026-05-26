from collections.abc import AsyncIterator

import redis.asyncio as aioredis
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import Settings
from src.domain.repositories import QueueRepo, RoomRepo, TicketRepo, WebSocketBroadcaster
from src.infrastructure.db.repositories import SQLAlchemyRoomRepo, SQLAlchemyTicketRepo
from src.infrastructure.redis.queue_manager import RedisQueueRepo, RoomConnectionManager
from src.services.admin import AdminService
from src.services.auth import AuthService
from src.services.queue import QueueService
from src.services.room import RoomService


class InfrastructureProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> Settings:
        return Settings()

    @provide
    async def redis(self, settings: Settings) -> AsyncIterator[aioredis.Redis]:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        yield client
        await client.aclose()

    @provide
    async def engine(self, settings: Settings) -> AsyncIterator[AsyncEngine]:
        eng = create_async_engine(settings.database_url, echo=False)
        yield eng
        await eng.dispose()

    @provide
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide
    def queue_repo(self, redis: aioredis.Redis, settings: Settings) -> QueueRepo:
        return RedisQueueRepo(redis, settings.queue_ttl)

    @provide
    def broadcaster(self, redis: aioredis.Redis) -> WebSocketBroadcaster:
        return RoomConnectionManager(redis)


class SessionProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def session(self, factory: async_sessionmaker) -> AsyncIterator[AsyncSession]:
        async with factory() as s:
            yield s

    @provide
    def room_repo(self, session: AsyncSession) -> RoomRepo:
        return SQLAlchemyRoomRepo(session)

    @provide
    def ticket_repo(self, session: AsyncSession) -> TicketRepo:
        return SQLAlchemyTicketRepo(session)


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def auth_service(self, settings: Settings) -> AuthService:
        return AuthService(settings)

    @provide
    def room_service(
        self,
        queue_repo: QueueRepo,
        room_repo: RoomRepo,
        auth_service: AuthService,
        broadcaster: WebSocketBroadcaster,
    ) -> RoomService:
        return RoomService(queue_repo, room_repo, auth_service, broadcaster)

    @provide
    def queue_service(
        self,
        queue_repo: QueueRepo,
        room_repo: RoomRepo,
        ticket_repo: TicketRepo,
        auth_service: AuthService,
        broadcaster: WebSocketBroadcaster,
    ) -> QueueService:
        return QueueService(queue_repo, room_repo, ticket_repo, auth_service, broadcaster)

    @provide
    def admin_service(
        self,
        queue_repo: QueueRepo,
        ticket_repo: TicketRepo,
        broadcaster: WebSocketBroadcaster,
    ) -> AdminService:
        return AdminService(queue_repo, ticket_repo, broadcaster)


def create_container() -> AsyncContainer:
    return make_async_container(
        InfrastructureProvider(),
        SessionProvider(),
        ServiceProvider(),
    )
