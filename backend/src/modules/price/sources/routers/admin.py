from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from src.common.bases.schemas import BaseMeta, PagerMeta
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.schemas import (
    ChartOutput,
    SourceChartMeta,
)
from src.modules.chart.ticker.interfaces import (
    ISourcePriceTickerService,
)
from src.modules.price.engine.interfaces import ICacheReaderService
from src.modules.price.sources.config.dependencies import (
    SourceID,
    SourceIDPath,
)
from src.modules.price.sources.domain.dtos import (
    SourceConfigUpdate,
    SourceCreate,
    SourceSearch,
    SourceUpdate,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.schemas import (
    SourceConfigOut,
    SourceOut,
    SourcePriceOut,
    SourceWithConfigOut,
    SymbolPricesOut,
)
from src.modules.price.sources.interfaces import (
    ISourceConfigService,
    ISourceService,
)
from src.modules.price.symbols.config.dependencies import SymbolIDPath
from src.web.response import APIResponse

# open until the auth module lands and brings the guard with it
router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
    route_class=DishkaRoute,
)

SourceResponse = APIResponse[SourceOut, None]
PagedSourceResponse = APIResponse[SourceOut, BaseMeta]
SourceWithConfigResponse = APIResponse[SourceWithConfigOut, None]
SourceConfigResponse = APIResponse[SourceConfigOut, None]
SymbolPricesResponse = APIResponse[SymbolPricesOut, None]
SourceChartResponse = APIResponse[ChartOutput, SourceChartMeta]


@router.post(
    "", response_model=SourceResponse, response_model_exclude_defaults=True
)
async def create_source(
    data: SourceCreate,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    source = await service.create(data)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.get(
    "", response_model=SourceResponse, response_model_exclude_defaults=True
)
async def get_sources(
    service: FromDishka[ISourceService],
) -> SourceResponse:
    sources = await service.get_all()
    return APIResponse.from_data(SourceOut.from_objs(sources))


@router.get(
    "/search",
    response_model=PagedSourceResponse,
    response_model_exclude_defaults=True,
)
async def search_sources(
    data: Annotated[SourceSearch, Query()],
    service: FromDishka[ISourceService],
) -> PagedSourceResponse:
    paged = await service.get_page(data)
    return APIResponse(
        success=True,
        data=SourceOut.from_objs(paged.items),
        meta=BaseMeta(
            pager=PagerMeta.from_total(
                data.page, data.per_page, paged.total_items
            )
        ),
    )


@router.get(
    "/configs",
    response_model=SourceWithConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_sources_with_config(
    service: FromDishka[ISourceService],
    switch: SourceSwitch | None = None,
) -> SourceWithConfigResponse:
    if switch is None:
        sources = await service.get_all_with_config()
    else:
        sources = await service.get_by_switch_with_config(switch)
    return APIResponse.from_data(SourceWithConfigOut.from_objs(sources))


@router.get(
    "/{id:int}",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def get_source(
    id: SourceID,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    source = await service.get_by_id(id)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.patch(
    "/{id:int}",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def update_source(
    id: SourceID,
    data: SourceUpdate,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    source = await service.update(id, data)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.delete(
    "/{id:int}",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def remove_source(
    id: SourceID,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    source = await service.remove(id)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.delete(
    "/{id:int}/error",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def clear_source_error(
    id: SourceID,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    source = await service.clear_error(id)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.get(
    "/{id:int}/config",
    response_model=SourceConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_source_config(
    id: SourceID,
    service: FromDishka[ISourceConfigService],
) -> SourceConfigResponse:
    config = await service.get_by_source_id(id)
    return APIResponse.from_data(SourceConfigOut.from_obj(config))


@router.patch(
    "/{id:int}/config",
    response_model=SourceConfigResponse,
    response_model_exclude_defaults=True,
)
async def update_source_config(
    id: SourceID,
    data: SourceConfigUpdate,
    service: FromDishka[ISourceConfigService],
) -> SourceConfigResponse:
    config = await service.update(id, data)
    return APIResponse.from_data(SourceConfigOut.from_obj(config))


@router.get(
    "/prices",
    response_model=SymbolPricesResponse,
    response_model_exclude_defaults=True,
)
async def get_source_prices(
    service: FromDishka[ICacheReaderService],
) -> SymbolPricesResponse:
    readings = await service.get_all()
    board = [
        SymbolPricesOut(symbol=symbol, prices=SourcePriceOut.from_objs(rows))
        for symbol, rows in readings.items()
    ]
    return APIResponse.from_data(board)


@router.get(
    "/{source_id:int}/symbols/{symbol_id:int}/chart",
    response_model=SourceChartResponse,
    response_model_exclude_defaults=True,
)
async def get_source_symbol_chart(
    source_id: SourceIDPath,
    symbol_id: SymbolIDPath,
    type: ChartType,
    service: FromDishka[ISourcePriceTickerService],
) -> SourceChartResponse:
    result = await service.get_source_chart_by_symbol(
        source_id, symbol_id, type
    )
    return APIResponse(success=True, data=result.data, meta=result.meta)
