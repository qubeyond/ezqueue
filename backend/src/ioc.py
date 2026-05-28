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
from src.domain.repositories import (
    EventPublisher,
    QueueRepository,
    RoomRepository,
    TicketRepository,
)
from src.infrastructure.db.repositories import SQLAlchemyRoomRepository, SQLAlchemyTicketRepository
from src.infrastructure.redis.connection_manager import RoomConnectionManager
from src.infrastructure.redis.queue_repo import RedisQueueRepository
from src.services.auth import AuthService
from src.services.room import RoomService
from src.services.visitor import VisitorService


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
    def queue_repo(self, redis: aioredis.Redis, settings: Settings) -> QueueRepository:
        return RedisQueueRepository(redis, settings.queue_ttl)

    @provide
    def publisher(self, redis: aioredis.Redis) -> EventPublisher:
        return RoomConnectionManager(redis)


class SessionProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def session(self, factory: async_sessionmaker) -> AsyncIterator[AsyncSession]:
        async with factory() as s:
            yield s

    @provide
    def room_repo(self, session: AsyncSession) -> RoomRepository:
        return SQLAlchemyRoomRepository(session)

    @provide
    def ticket_repo(self, session: AsyncSession) -> TicketRepository:
        return SQLAlchemyTicketRepository(session)


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def auth_service(self, settings: Settings) -> AuthService:
        return AuthService(settings)

    @provide
    def room_service(
        self,
        queue_repo: QueueRepository,
        room_repo: RoomRepository,
        ticket_repo: TicketRepository,
        auth_service: AuthService,
        publisher: EventPublisher,
    ) -> RoomService:
        return RoomService(queue_repo, room_repo, ticket_repo, auth_service, publisher)

    @provide
    def visitor_service(
        self,
        queue_repo: QueueRepository,
        ticket_repo: TicketRepository,
        auth_service: AuthService,
        publisher: EventPublisher,
    ) -> VisitorService:
        return VisitorService(queue_repo, ticket_repo, auth_service, publisher)


def create_container() -> AsyncContainer:
    return make_async_container(
        InfrastructureProvider(),
        SessionProvider(),
        ServiceProvider(),
    )
