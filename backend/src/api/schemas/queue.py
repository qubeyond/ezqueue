from typing import Annotated

from pydantic import BaseModel, Field

RoomId = Annotated[str, Field(min_length=1, max_length=10)]
QueueLabel = Annotated[str, Field(min_length=1, max_length=4, pattern=r"^[A-Z]+$")]


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
