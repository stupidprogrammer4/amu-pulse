from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel

from src.common.utils import currency_utils, date_utils
from src.modules.price.engine.domain.enums import SelectionReason


class PriceResult(BaseModel):
    buy_price: int
    sell_price: int
    price: int
    buy_spread_rial: int
    sell_spread_rial: int
    buy_spread_rate: Decimal
    sell_spread_rate: Decimal
    priced_at: datetime


class AssetPriceResult(PriceResult):
    asset_id: int


class SourcePriceResult(PriceResult):
    symbol_id: int
    source_id: int
    is_selected: bool = False
    reason: SelectionReason | None = None

    @classmethod
    def from_sides(
        cls,
        source_id: int,
        symbol_id: int,
        selling: int,
        buying: int,
    ) -> Self:
        selling = currency_utils.round_rial(selling)
        buying = currency_utils.round_rial(buying)
        price = currency_utils.round_rial((selling + buying) / 2)
        sell_spread = selling - price
        buy_spread = price - buying
        divisor = Decimal(price) if price else Decimal(1)
        result = cls(
            source_id=source_id,
            symbol_id=symbol_id,
            sell_price=selling,
            buy_price=buying,
            price=price,
            sell_spread_rial=sell_spread,
            buy_spread_rial=buy_spread,
            sell_spread_rate=Decimal(sell_spread) / divisor,
            buy_spread_rate=Decimal(buy_spread) / divisor,
            priced_at=date_utils.utc_now(),
        )
        return result


class BubbleResult(BaseModel):
    asset_id: int
    amount: int
    priced_at: datetime


class SourceBubbleResult(BubbleResult):
    source_id: int


class PriceWindowResult(BaseModel):
    open: int
    high: int
    low: int
    close: int
    bucket: datetime


class AssetPriceWindowResult(PriceWindowResult):
    asset_id: int


class SourcePriceWindowResult(PriceWindowResult):
    symbol_id: int
    source_id: int
