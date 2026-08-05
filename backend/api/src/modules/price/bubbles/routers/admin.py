from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.modules.identity.auth.config.dependencies import (
    admin_required,
)
from src.modules.price.bubbles.config.dependencies import BubbleID
from src.modules.price.bubbles.domain.dtos import (
    BubbleConfigUpdate,
    BubbleCreate,
    BubbleUpdate,
)
from src.modules.price.bubbles.domain.schemas import (
    BubbleConfigOut,
    BubbleOut,
    BubbleWithConfigOut,
)
from src.modules.price.bubbles.interfaces import (
    IBubbleConfigService,
    IBubbleService,
)
from src.web.response import APIResponse

# every route here is an admin panel route; the guard sits on the
# router so no handler can be added without it
router = APIRouter(
    prefix="/admin/bubbles",
    tags=["Admin Bubbles"],
    route_class=DishkaRoute,
    dependencies=[admin_required],
)

BubbleResponse = APIResponse[BubbleOut, None]
BubbleWithConfigResponse = APIResponse[BubbleWithConfigOut, None]
BubbleConfigResponse = APIResponse[BubbleConfigOut, None]


@router.post(
    "", response_model=BubbleResponse, response_model_exclude_defaults=True
)
async def create_bubble(
    data: BubbleCreate,
    service: FromDishka[IBubbleService],
) -> BubbleResponse:
    bubble = await service.create(data)
    return APIResponse.from_data(BubbleOut.from_obj(bubble))


@router.get(
    "", response_model=BubbleResponse, response_model_exclude_defaults=True
)
async def get_bubbles(
    service: FromDishka[IBubbleService],
) -> BubbleResponse:
    bubbles = await service.get_all()
    return APIResponse.from_data(BubbleOut.from_objs(bubbles))


@router.get(
    "/configs",
    response_model=BubbleWithConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_bubbles_with_config(
    service: FromDishka[IBubbleService],
) -> BubbleWithConfigResponse:
    bubbles = await service.get_all_with_config()
    return APIResponse.from_data(BubbleWithConfigOut.from_objs(bubbles))


@router.get(
    "/{id:int}",
    response_model=BubbleResponse,
    response_model_exclude_defaults=True,
)
async def get_bubble(
    id: BubbleID,
    service: FromDishka[IBubbleService],
) -> BubbleResponse:
    bubble = await service.get_by_id(id)
    return APIResponse.from_data(BubbleOut.from_obj(bubble))


@router.patch(
    "/{id:int}",
    response_model=BubbleResponse,
    response_model_exclude_defaults=True,
)
async def update_bubble(
    id: BubbleID,
    data: BubbleUpdate,
    service: FromDishka[IBubbleService],
) -> BubbleResponse:
    bubble = await service.update(id, data)
    return APIResponse.from_data(BubbleOut.from_obj(bubble))


@router.delete(
    "/{id:int}",
    response_model=BubbleResponse,
    response_model_exclude_defaults=True,
)
async def remove_bubble(
    id: BubbleID,
    service: FromDishka[IBubbleService],
) -> BubbleResponse:
    bubble = await service.remove(id)
    return APIResponse.from_data(BubbleOut.from_obj(bubble))


@router.get(
    "/{id:int}/config",
    response_model=BubbleConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_bubble_config(
    id: BubbleID,
    service: FromDishka[IBubbleConfigService],
) -> BubbleConfigResponse:
    config = await service.get_by_bubble_id(id)
    return APIResponse.from_data(BubbleConfigOut.from_obj(config))


@router.patch(
    "/{id:int}/config",
    response_model=BubbleConfigResponse,
    response_model_exclude_defaults=True,
)
async def update_bubble_config(
    id: BubbleID,
    data: BubbleConfigUpdate,
    service: FromDishka[IBubbleConfigService],
) -> BubbleConfigResponse:
    config = await service.update(id, data)
    return APIResponse.from_data(BubbleConfigOut.from_obj(config))
