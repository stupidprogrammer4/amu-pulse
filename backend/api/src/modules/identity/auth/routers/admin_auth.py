from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.modules.identity.admins.domain.schemas import AdminOut
from src.modules.identity.admins.interfaces import IAdminService
from src.modules.identity.auth.config.dependencies import CurrentAdmin
from src.modules.identity.auth.domain.dtos import AdminLoginIn, RefreshIn
from src.modules.identity.auth.domain.schemas import AdminAuthOut
from src.modules.identity.auth.interfaces import IAdminAuthService
from src.web.response import APIResponse

router = APIRouter(prefix="/auth", tags=["Auth"], route_class=DishkaRoute)

AdminAuthResponse = APIResponse[AdminAuthOut, None]
AdminResponse = APIResponse[AdminOut, None]


@router.post(
    "/admins/login",
    response_model=AdminAuthResponse,
    response_model_exclude_defaults=True,
)
async def login_admin(
    data: AdminLoginIn,
    service: FromDishka[IAdminAuthService],
) -> AdminAuthResponse:
    auth = await service.login(data.username, data.password)
    return APIResponse.from_data(AdminAuthOut.from_auth(auth))


@router.post(
    "/admins/refresh",
    response_model=AdminAuthResponse,
    response_model_exclude_defaults=True,
)
async def refresh_admin(
    data: RefreshIn,
    service: FromDishka[IAdminAuthService],
) -> AdminAuthResponse:
    auth = await service.refresh(data.refresh_token)
    return APIResponse.from_data(AdminAuthOut.from_auth(auth))


@router.get(
    "/admins/me",
    response_model=AdminResponse,
    response_model_exclude_defaults=True,
)
async def get_current_admin(
    principal: CurrentAdmin,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.get_by_id(principal.id)
    return APIResponse.from_data(AdminOut.from_obj(admin))
