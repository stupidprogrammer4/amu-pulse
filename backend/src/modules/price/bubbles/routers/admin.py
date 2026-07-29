from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

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

# open until the auth module lands and brings the guard with it
router = APIRouter(
    prefix="/bubbles",
    tags=["Bubbles"],
    route_class=DishkaRoute,
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
    """
    Desc: Create a bubble together with its default config.
    Args:
        data (BubbleCreate): Validated payload to persist.
        service (IBubbleService): The bubble service.
    Returns:
        return (BubbleResponse): The created bubble.
    """
    bubble = await service.create(data)
    return APIResponse.from_data(BubbleOut.from_obj(bubble))


@router.get(
    "", response_model=BubbleResponse, response_model_exclude_defaults=True
)
async def get_bubbles(
    service: FromDishka[IBubbleService],
) -> BubbleResponse:
    """
    Desc: Get every bubble.
    Args:
        service (IBubbleService): The bubble service.
    Returns:
        return (BubbleResponse): All bubbles.
    """
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
    """
    Desc: Get every bubble with its config.
    Args:
        service (IBubbleService): The bubble service.
    Returns:
        return (BubbleWithConfigResponse): Each bubble with its config.
    """
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
    """
    Desc: Get a bubble by id.
    Args:
        id (int): ID of the bubble.
        service (IBubbleService): The bubble service.
    Returns:
        return (BubbleResponse): The found bubble.
    """
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
    """
    Desc: Patch a bubble by id.
    Args:
        id (int): ID of the bubble.
        data (BubbleUpdate): The fields to change.
        service (IBubbleService): The bubble service.
    Returns:
        return (BubbleResponse): The updated bubble.
    """
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
    """
    Desc: Delete a bubble by id, its config cascading with it.
    Args:
        id (int): ID of the bubble.
        service (IBubbleService): The bubble service.
    Returns:
        return (BubbleResponse): The deleted bubble.
    """
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
    """
    Desc: Get a bubble's config.
    Args:
        id (int): ID of the bubble.
        service (IBubbleConfigService): The bubble config service.
    Returns:
        return (BubbleConfigResponse): The found config.
    """
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
    """
    Desc: Patch a bubble's config.
    Args:
        id (int): ID of the bubble.
        data (BubbleConfigUpdate): The fields to change.
        service (IBubbleConfigService): The bubble config service.
    Returns:
        return (BubbleConfigResponse): The updated config.
    """
    config = await service.update(id, data)
    return APIResponse.from_data(BubbleConfigOut.from_obj(config))
