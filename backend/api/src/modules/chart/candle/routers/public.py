from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from src.modules.chart.candle.domain.dtos import ParamDTO, SourceParamDTO
from src.modules.chart.candle.domain.schemas import CandleChartOut
from src.modules.chart.candle.interfaces import (
    ICandleService,
    ISourceCandleService,
)
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.schemas import ChartOutput
from src.modules.chart.ticker.interfaces import IPriceTickerService
from src.modules.price.assets.config.dependencies import AssetID
from src.modules.price.assets.domain.schemas import AssetMeta
from src.modules.price.sources.config.dependencies import SourceID
from src.modules.price.sources.domain.schemas import SourceMeta
from src.web.response import APIResponse

# no guard, unlike /admin/candles: a chart is public the same way a price is
router = APIRouter(
    prefix="/charts",
    tags=["Charts"],
    route_class=DishkaRoute,
)

CandleChartResponse = APIResponse[CandleChartOut, AssetMeta]
SourceCandleChartResponse = APIResponse[CandleChartOut, SourceMeta]
TickerResponse = APIResponse[ChartOutput, AssetMeta]


@router.get(
    "/assets/{id:int}/candles",
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
    "/assets/{id:int}/ticker",
    response_model=TickerResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_ticker(
    id: AssetID,
    service: FromDishka[IPriceTickerService],
    type: ChartType = ChartType.DAILY,
) -> TickerResponse:
    result = await service.get_chart(id, type)
    return APIResponse(success=True, data=result.data, meta=result.meta)


@router.get(
    "/sources/{id:int}/candles",
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
