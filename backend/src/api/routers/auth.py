from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Cookie, HTTPException, Query, Request, Response

from src.api.limiter import limiter
from src.api.schemas.auth import TokenResponse
from src.services.auth import REFRESH_COOKIE, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
@limiter.limit("20/minute")
@inject
async def get_token(
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    fingerprint: Annotated[str, Query(min_length=8, max_length=128, pattern=r"^[\x21-\x7E]+$")],
):
    access_token = auth_service.create_token(fingerprint=fingerprint, role="user")

    auth_service.set_refresh_cookie(response, fingerprint)

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
@inject
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh токен отсутствует")

    payload = auth_service.decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Невалидный тип токена")

    fingerprint: str = payload["sub"]
    access_token = auth_service.create_token(fingerprint=fingerprint, role="user")

    auth_service.set_refresh_cookie(response, fingerprint)

    return TokenResponse(access_token=access_token)


@router.post("/logout")
@inject
async def logout(
    request: Request,
    response: Response,
):
    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")

    return {"status": "ok"}
