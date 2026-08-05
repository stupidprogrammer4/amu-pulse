from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.schemas import (
    PublicAssetBubblesOut,
    PublicBubbleOut,
    PublicPriceOut,
    PublicSymbolPricesOut,
)
from src.modules.price.engine.interfaces import ICacheReaderService
from src.modules.price.symbols.domain.enums import SymbolCode
from src.web.response import APIResponse

# no guard, unlike everything under /admin: reading a price is what the site
# is for. Every route here answers off the price cache, so a crowd of
# visitors never reaches Postgres.
router = APIRouter(
    prefix="/prices",
    tags=["Prices"],
    route_class=DishkaRoute,
)

SymbolPricesResponse = APIResponse[PublicSymbolPricesOut, None]
AssetBubblesResponse = APIResponse[PublicAssetBubblesOut, None]


@router.get(
    "",
    response_model=SymbolPricesResponse,
    response_model_exclude_defaults=True,
)
async def get_prices(
    service: FromDishka[ICacheReaderService],
) -> SymbolPricesResponse:
    prices = await service.get_all()
    return APIResponse.from_data(
        [
            PublicSymbolPricesOut(
                symbol=symbol, prices=PublicPriceOut.from_objs(quotes)
            )
            for symbol, quotes in prices.items()
        ]
    )


# before /{symbol}, or the router reads "bubbles" as a symbol code
@router.get(
    "/bubbles",
    response_model=AssetBubblesResponse,
    response_model_exclude_defaults=True,
)
async def get_bubbles(
    service: FromDishka[ICacheReaderService],
) -> AssetBubblesResponse:
    bubbles = await service.get_all_bubbles()
    return APIResponse.from_data(
        [
            PublicAssetBubblesOut(
                asset=asset, bubbles=PublicBubbleOut.from_objs(rows)
            )
            for asset, rows in bubbles.items()
        ]
    )


@router.get(
    "/bubbles/{code}",
    response_model=AssetBubblesResponse,
    response_model_exclude_defaults=True,
)
async def get_asset_bubbles(
    code: AssetCode,
    service: FromDishka[ICacheReaderService],
) -> AssetBubblesResponse:
    rows = await service.get_bubbles_by_asset(code)
    return APIResponse.from_data(
        PublicAssetBubblesOut(
            asset=code, bubbles=PublicBubbleOut.from_objs(rows)
        )
    )


@router.get(
    "/{symbol}",
    response_model=SymbolPricesResponse,
    response_model_exclude_defaults=True,
)
async def get_symbol_prices(
    symbol: SymbolCode,
    service: FromDishka[ICacheReaderService],
) -> SymbolPricesResponse:
    quotes = await service.get_by_symbol(symbol)
    return APIResponse.from_data(
        PublicSymbolPricesOut(
            symbol=symbol, prices=PublicPriceOut.from_objs(quotes)
        )
    )
