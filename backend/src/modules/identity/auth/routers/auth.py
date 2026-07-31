from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Request

from src.modules.identity.auth.domain.dtos import (
    TokenRefresh,
    UserLogin,
    UserRegister,
)
from src.modules.identity.auth.domain.results import AuthResult
from src.modules.identity.auth.domain.schemas import AuthOut, UserOut
from src.modules.identity.auth.interfaces import IAuthService
from src.web.response import APIResponse

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    route_class=DishkaRoute,
)

AuthResponse = APIResponse[AuthOut, None]
EmptyResponse = APIResponse[None, None]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _device(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _to_auth_out(result: AuthResult) -> AuthOut:
    """
    Desc: Map an auth result to its wire representation.
    Args:
        result (AuthResult): The user and the tokens issued for them.
    Returns:
        return (AuthOut): The user, the tokens and the token type.
    """
    auth_out = AuthOut(
        user=UserOut.from_obj(result.user),
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
    )
    return auth_out


@router.post(
    "/register",
    response_model=AuthResponse,
    response_model_exclude_defaults=True,
)
async def register(
    data: UserRegister,
    request: Request,
    service: FromDishka[IAuthService],
) -> AuthResponse:
    result = await service.register(
        data, ip=_client_ip(request), device=_device(request)
    )
    return APIResponse.from_data(_to_auth_out(result))


@router.post(
    "/login",
    response_model=AuthResponse,
    response_model_exclude_defaults=True,
)
async def login(
    data: UserLogin,
    request: Request,
    service: FromDishka[IAuthService],
) -> AuthResponse:
    result = await service.login(
        data, ip=_client_ip(request), device=_device(request)
    )
    return APIResponse.from_data(_to_auth_out(result))


@router.post(
    "/refresh",
    response_model=AuthResponse,
    response_model_exclude_defaults=True,
)
async def refresh(
    data: TokenRefresh,
    request: Request,
    service: FromDishka[IAuthService],
) -> AuthResponse:
    result = await service.refresh(
        data, ip=_client_ip(request), device=_device(request)
    )
    return APIResponse.from_data(_to_auth_out(result))


@router.post(
    "/logout",
    response_model=EmptyResponse,
    response_model_exclude_defaults=True,
)
async def logout(
    data: TokenRefresh,
    service: FromDishka[IAuthService],
) -> EmptyResponse:
    await service.logout(data)
    return APIResponse.from_data(None)