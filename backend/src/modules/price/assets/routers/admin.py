from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.modules.price.assets.config.dependencies import AssetID
from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetUpdate,
)
from src.modules.price.assets.domain.schemas import (
    AssetConfigOut,
    AssetOut,
    AssetWithConfigOut,
)
from src.modules.price.assets.interfaces import (
    IAssetConfigService,
    IAssetService,
)
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
