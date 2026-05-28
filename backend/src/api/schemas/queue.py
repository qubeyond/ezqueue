from pydantic import BaseModel, Field

from src.api.schemas.common import QueueLabel, RoomId


class JoinRequest(BaseModel):
    room_id: RoomId
    queue_label: QueueLabel | None = None


class TakeTicketResponse(BaseModel):
    is_admin: bool
    room_id: str | None = None
    queue_label: str | None = None
    access_token: str | None = None
    ticket: str | None = None
    position: int | None = Field(default=None, ge=1)


class LeaveQueueResponse(BaseModel):
    status: str
