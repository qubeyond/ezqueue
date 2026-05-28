from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: FromDishka[AuthService],
) -> dict:
    return auth_service.verify_user(credentials)


async def require_admin(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Требуются права администратора")

    return user


async def require_room_admin(
    user: Annotated[dict, Depends(require_admin)],
) -> dict:
    return user
