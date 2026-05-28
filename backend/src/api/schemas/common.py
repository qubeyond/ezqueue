from typing import Annotated

from pydantic import Field

RoomId = Annotated[str, Field(min_length=1, max_length=10)]
QueueLabel = Annotated[str, Field(min_length=1, max_length=1, pattern=r"^[ABCDEFGHJK]$")]
