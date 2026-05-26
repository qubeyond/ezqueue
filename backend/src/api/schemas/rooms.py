from pydantic import BaseModel, Field


class RoomCreateResponse(BaseModel):
    room_id: str
    access_token: str
    token_type: str = Field(default="bearer")


class RoomCloseResponse(BaseModel):
    status: str


class QueueInfo(BaseModel):
    label: str
    length: int = Field(ge=0)
    status: str
    current_ticket: str


class ClientContext(BaseModel):
    ticket_label: str
    queue_label: str
    position_label: str
    should_redirect: bool


class AdminContext(BaseModel):
    queues: list[QueueInfo]
    elapsed_time: int = Field(default=0, ge=0)


class RoomStateResponse(BaseModel):
    room_closed: bool
    room_id: str
    current_status: str | None = None
    elapsed_time: int | None = None
    avg_serve_seconds: int | None = None
    client_context: ClientContext | None = None
    admin_context: AdminContext | None = None
