from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.schemas import SourceChartOutput
from src.modules.chart.ticker.interfaces import (
    ISourcePriceTickerService,
)
from src.modules.identity.auth.config.dependencies import (
    admin_required,
)
from src.modules.price.assets.config.dependencies import AssetID
from src.modules.price.sources.domain.schemas import SourceMeta
from src.modules.price.symbols.config.dependencies import SymbolID
from src.modules.price.symbols.domain.dtos import SymbolCreate, SymbolUpdate
from src.modules.price.symbols.domain.schemas import SymbolOut
from src.modules.price.symbols.interfaces import ISymbolService
from src.web.response import APIResponse

# every route here is an admin panel route; the guard sits on the
# router so no handler can be added without it
router = APIRouter(
    prefix="/panel/symbols",
    tags=["Panel Symbols"],
    route_class=DishkaRoute,
    dependencies=[admin_required],
)

SymbolResponse = APIResponse[SymbolOut, None]
SymbolChartResponse = APIResponse[SourceChartOutput, SourceMeta]


@router.post(
    "", response_model=SymbolResponse, response_model_exclude_defaults=True
)
async def create_symbol(
    data: SymbolCreate,
    service: FromDishka[ISymbolService],
) -> SymbolResponse:
    symbol = await service.create(data)
    return APIResponse.from_data(SymbolOut.from_obj(symbol))


@router.get(
    "", response_model=SymbolResponse, response_model_exclude_defaults=True
)
async def get_symbols(
    service: FromDishka[ISymbolService],
) -> SymbolResponse:
    symbols = await service.get_all()
    return APIResponse.from_data(SymbolOut.from_objs(symbols))


@router.get(
    "/assets/{asset_id:int}",
    response_model=SymbolResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_symbols(
    asset_id: AssetID,
    service: FromDishka[ISymbolService],
) -> SymbolResponse:
    symbols = await service.get_by_asset_id(asset_id)
    return APIResponse.from_data(SymbolOut.from_objs(symbols))


@router.get(
    "/{id:int}",
    response_model=SymbolResponse,
    response_model_exclude_defaults=True,
)
async def get_symbol(
    id: SymbolID,
    service: FromDishka[ISymbolService],
) -> SymbolResponse:
    symbol = await service.get_by_id(id)
    return APIResponse.from_data(SymbolOut.from_obj(symbol))


@router.patch(
    "/{id:int}",
    response_model=SymbolResponse,
    response_model_exclude_defaults=True,
)
async def update_symbol(
    id: SymbolID,
    data: SymbolUpdate,
    service: FromDishka[ISymbolService],
) -> SymbolResponse:
    symbol = await service.update(id, data)
    return APIResponse.from_data(SymbolOut.from_obj(symbol))


@router.delete(
    "/{id:int}",
    response_model=SymbolResponse,
    response_model_exclude_defaults=True,
)
async def remove_symbol(
    id: SymbolID,
    service: FromDishka[ISymbolService],
) -> SymbolResponse:
    symbol = await service.remove(id)
    return APIResponse.from_data(SymbolOut.from_obj(symbol))


@router.get(
    "/{id:int}/chart",
    response_model=SymbolChartResponse,
    response_model_exclude_defaults=True,
)
async def get_symbol_chart(
    id: SymbolID,
    type: ChartType,
    service: FromDishka[ISourcePriceTickerService],
) -> SymbolChartResponse:
    result = await service.get_chart_by_symbol(id, type)
    return APIResponse(success=True, data=result.data, meta=result.meta)
