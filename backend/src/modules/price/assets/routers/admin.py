from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.common.errors.exceptions import NotFoundException
from src.core import resources
from src.modules.price.assets.config.dependencies import (
    AssetID,
    AssetSwitchID,
)
from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetSwitchBatchCreate,
    AssetSwitchBatchDelete,
    AssetSwitchBatchUpdate,
    AssetSwitchCreate,
    AssetSwitchPriorityUpdate,
    AssetSwitchUpdate,
    AssetUpdate,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.schemas import (
    AssetConfigOut,
    AssetOut,
    AssetPriceOut,
    AssetSwitchOut,
    AssetWithConfigOut,
    RepriceOut,
)
from src.modules.price.assets.interfaces import (
    IAssetConfigService,
    IAssetService,
    IAssetSwitchService,
)
from src.modules.price.calculator.interfaces import ICacheReaderService
from src.modules.price.calculator.tasks.price import reprice_asset as reprice
from src.web.response import APIResponse

# open until the auth module lands and brings the guard with it
router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
    route_class=DishkaRoute,
)

AssetResponse = APIResponse[AssetOut, None]
AssetWithConfigResponse = APIResponse[AssetWithConfigOut, None]
AssetConfigResponse = APIResponse[AssetConfigOut, None]
AssetSwitchResponse = APIResponse[AssetSwitchOut, None]
AssetPriceResponse = APIResponse[AssetPriceOut, None]
RepriceResponse = APIResponse[RepriceOut, None]


@router.post(
    "", response_model=AssetResponse, response_model_exclude_defaults=True
)
async def create_asset(
    data: AssetCreate,
    service: FromDishka[IAssetService],
) -> AssetResponse:
    asset = await service.create(data)
    return APIResponse.from_data(AssetOut.from_obj(asset))


@router.get(
    "", response_model=AssetResponse, response_model_exclude_defaults=True
)
async def get_assets(
    service: FromDishka[IAssetService],
) -> AssetResponse:
    assets = await service.get_all()
    return APIResponse.from_data(AssetOut.from_objs(assets))


@router.get(
    "/configs",
    response_model=AssetWithConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_assets_with_config(
    service: FromDishka[IAssetService],
) -> AssetWithConfigResponse:
    assets = await service.get_all_with_config()
    return APIResponse.from_data(AssetWithConfigOut.from_objs(assets))


@router.get(
    "/{id:int}",
    response_model=AssetResponse,
    response_model_exclude_defaults=True,
)
async def get_asset(
    id: AssetID,
    service: FromDishka[IAssetService],
) -> AssetResponse:
    asset = await service.get_by_id(id)
    return APIResponse.from_data(AssetOut.from_obj(asset))


@router.patch(
    "/{id:int}",
    response_model=AssetResponse,
    response_model_exclude_defaults=True,
)
async def update_asset(
    id: AssetID,
    data: AssetUpdate,
    service: FromDishka[IAssetService],
) -> AssetResponse:
    asset = await service.update(id, data)
    return APIResponse.from_data(AssetOut.from_obj(asset))


@router.delete(
    "/{id:int}",
    response_model=AssetResponse,
    response_model_exclude_defaults=True,
)
async def remove_asset(
    id: AssetID,
    service: FromDishka[IAssetService],
) -> AssetResponse:
    asset = await service.remove(id)
    return APIResponse.from_data(AssetOut.from_obj(asset))


@router.get(
    "/{id:int}/config",
    response_model=AssetConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_config(
    id: AssetID,
    service: FromDishka[IAssetConfigService],
) -> AssetConfigResponse:
    config = await service.get_by_asset_id(id)
    return APIResponse.from_data(AssetConfigOut.from_obj(config))


@router.patch(
    "/{id:int}/config",
    response_model=AssetConfigResponse,
    response_model_exclude_defaults=True,
)
async def update_asset_config(
    id: AssetID,
    data: AssetConfigUpdate,
    service: FromDishka[IAssetConfigService],
) -> AssetConfigResponse:
    config = await service.update(id, data)
    return APIResponse.from_data(AssetConfigOut.from_obj(config))


@router.get(
    "/{asset_id:int}/switches",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_switches(
    asset_id: AssetID,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switches = await service.get_by_asset_id(asset_id)
    return APIResponse.from_data(AssetSwitchOut.from_objs(switches))


@router.post(
    "/{asset_id:int}/switches",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def create_asset_switch(
    asset_id: AssetID,
    data: AssetSwitchCreate,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switch = await service.create(asset_id, data)
    return APIResponse.from_data(AssetSwitchOut.from_obj(switch))


@router.post(
    "/{asset_id:int}/switches/batch",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def batch_create_asset_switches(
    asset_id: AssetID,
    data: AssetSwitchBatchCreate,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switches = await service.batch_create(asset_id, data)
    return APIResponse.from_data(AssetSwitchOut.from_objs(switches))


@router.put(
    "/{asset_id:int}/switches/batch",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def batch_update_asset_switches(
    asset_id: AssetID,
    data: AssetSwitchBatchUpdate,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switches = await service.batch_update(asset_id, data)
    return APIResponse.from_data(AssetSwitchOut.from_objs(switches))


@router.patch(
    "/{asset_id:int}/switches/batch",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def set_asset_switches_priority(
    asset_id: AssetID,
    data: AssetSwitchPriorityUpdate,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switches = await service.set_priority(asset_id, data)
    return APIResponse.from_data(AssetSwitchOut.from_objs(switches))


@router.delete(
    "/{asset_id:int}/switches/batch",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def batch_remove_asset_switches(
    asset_id: AssetID,
    data: AssetSwitchBatchDelete,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switches = await service.batch_remove(asset_id, data)
    return APIResponse.from_data(AssetSwitchOut.from_objs(switches))


@router.patch(
    "/{asset_id:int}/switches/{asset_switch_id:int}",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def update_asset_switch(
    asset_id: AssetID,
    asset_switch_id: AssetSwitchID,
    data: AssetSwitchUpdate,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switch = await service.update(asset_id, asset_switch_id, data)
    return APIResponse.from_data(AssetSwitchOut.from_obj(switch))


@router.delete(
    "/{asset_id:int}/switches/{asset_switch_id:int}",
    response_model=AssetSwitchResponse,
    response_model_exclude_defaults=True,
)
async def remove_asset_switch(
    asset_id: AssetID,
    asset_switch_id: AssetSwitchID,
    service: FromDishka[IAssetSwitchService],
) -> AssetSwitchResponse:
    switch = await service.remove(asset_id, asset_switch_id)
    return APIResponse.from_data(AssetSwitchOut.from_obj(switch))


@router.post(
    "/{asset_code}/reprice",
    response_model=RepriceResponse,
    response_model_exclude_defaults=True,
)
async def reprice_asset(asset_code: AssetCode) -> RepriceResponse:
    # off the request's own time: the answer is the job, not the price
    job = await reprice.kiq(asset_code)  # type: ignore[call-arg]
    return APIResponse.from_data(RepriceOut(task_id=job.task_id))


@router.get(
    "/{asset_code}/price",
    response_model=AssetPriceResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_price(
    asset_code: AssetCode,
    service: FromDishka[ICacheReaderService],
) -> AssetPriceResponse:
    price = await service.get_price(asset_code)
    if price is None:
        raise NotFoundException(
            identifier="code",
            identifier_value=asset_code.value,
            message=f"Cannot find Price by code with value {asset_code.value}",
            message_code=resources.NOT_FOUND_ERROR,
            entity="Price",
        )
    return APIResponse.from_data(AssetPriceOut.from_obj(price))
