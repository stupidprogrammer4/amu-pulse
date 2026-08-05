from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from src.modules.chart.candle.domain.dtos import ParamDTO, SourceParamDTO
from src.modules.chart.candle.domain.schemas import CandleChartOut
from src.modules.chart.candle.interfaces import (
    ICandleService,
    ISourceCandleService,
)
from src.modules.identity.auth.config.dependencies import (
    admin_required,
)
from src.modules.price.assets.config.dependencies import AssetID
from src.modules.price.assets.domain.schemas import AssetMeta
from src.modules.price.sources.config.dependencies import SourceID
from src.modules.price.sources.domain.schemas import SourceMeta
from src.web.response import APIResponse

# every route here is an admin panel route; the guard sits on the
# router so no handler can be added without it
router = APIRouter(
    prefix="/panel/candles",
    tags=["Panel Candles"],
    route_class=DishkaRoute,
    dependencies=[admin_required],
)

CandleChartResponse = APIResponse[CandleChartOut, AssetMeta]
SourceCandleChartResponse = APIResponse[CandleChartOut, SourceMeta]


@router.get(
    "/assets/{id:int}",
    response_model=CandleChartResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_candles(
    id: AssetID,
    param: Annotated[ParamDTO, Query()],
    service: FromDishka[ICandleService],
) -> CandleChartResponse:
    result = await service.get_candle(id, param)
    return APIResponse(success=True, data=result.data, meta=result.meta)


@router.get(
    "/sources/{id:int}",
    response_model=SourceCandleChartResponse,
    response_model_exclude_defaults=True,
)
async def get_source_candles(
    id: SourceID,
    param: Annotated[SourceParamDTO, Query()],
    service: FromDishka[ISourceCandleService],
) -> SourceCandleChartResponse:
    result = await service.get_candle(id, param)
    return APIResponse(success=True, data=result.data, meta=result.meta)
