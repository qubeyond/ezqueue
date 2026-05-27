from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class TicketEventEntity:
    room_id: str
    queue_label: str
    ticket_num: str
    user_fingerprint: str
    joined_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    called_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def wait_seconds(self) -> int | None:
        if self.called_at:
            return int((self.called_at - self.joined_at).total_seconds())
        return None

    @property
    def serve_seconds(self) -> int | None:
        if self.called_at and self.completed_at:
            return int((self.completed_at - self.called_at).total_seconds())
        return None


@dataclass
class RoomCreated:
    room_id: str
    access_token: str


@dataclass
class RoomClosed:
    status: str


@dataclass
class TicketTaken:
    is_admin: bool
    room_id: str | None = None
    queue_label: str | None = None
    access_token: str | None = None
    ticket: str | None = None
    position: int | None = None


@dataclass
class QueueLeft:
    status: str


@dataclass
class NextCalled:
    queue_label: str
    ticket: str


@dataclass
class ServingCompleted:
    pass


@dataclass
class QueueAdded:
    queue_label: str


@dataclass
class QueueRemoved:
    queue_label: str


@dataclass
class TicketTimeline:
    ticket: str
    queue_label: str
    joined_at: datetime
    wait_seconds: int | None
    serve_seconds: int | None


@dataclass
class RoomStats:
    room_id: str
    total_tickets: int
    completed: int
    avg_serve_seconds: int
    timeline: list[TicketTimeline]
