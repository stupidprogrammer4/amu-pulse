from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.modules.identity.auth.config.dependencies import CurrentUser
from src.modules.identity.auth.domain.schemas import UserOut
from src.modules.identity.auth.interfaces import IAuthService
from src.web.response import APIResponse

router = APIRouter(
    prefix="/account",
    tags=["Account"],
    route_class=DishkaRoute,
)

UserResponse = APIResponse[UserOut, None]


@router.get(
    "/me",
    response_model=UserResponse,
    response_model_exclude_defaults=True,
)
async def get_me(
    user: CurrentUser,
    service: FromDishka[IAuthService],
) -> UserResponse:
    found = await service.get_by_id(user.id)
    return APIResponse.from_data(UserOut.from_obj(found))