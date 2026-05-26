from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

RoomId = Annotated[str, Field(min_length=1, max_length=10)]
QueueLabel = Annotated[str, Field(min_length=1, max_length=4, pattern=r"^[A-Z]+$")]


class QueueAction(BaseModel):
    room_id: RoomId
    queue_label: QueueLabel = Field(default="A")


class AddQueueRequest(BaseModel):
    room_id: RoomId


class RemoveQueueRequest(BaseModel):
    room_id: RoomId
    queue_label: QueueLabel


class CallNextResponse(BaseModel):
    status: str = Field(default="called")
    queue_label: str
    ticket: str


class CompleteServingResponse(BaseModel):
    status: str = Field(default="completed")


class QueueMutationResponse(BaseModel):
    status: str
    queue_label: str


class TicketTimeline(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket: str
    queue_label: str
    joined_at: datetime
    wait_seconds: int | None = None
    serve_seconds: int | None = None


class RoomStatsResponse(BaseModel):
    room_id: str
    total_tickets: int = Field(ge=0)
    completed: int = Field(ge=0)
    avg_serve_seconds: int = Field(ge=0)
    timeline: list[TicketTimeline]
