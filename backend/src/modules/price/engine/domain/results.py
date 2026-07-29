from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field

from src.common.utils import date_utils
from src.modules.price.engine.domain.enums import ComputationKind


class SupplierComputation(BaseModel):
    kind: Literal[ComputationKind.SUPPLIER] = ComputationKind.SUPPLIER
    selling_mazane: int
    buying_mazane: int
    mazane_factor: Decimal
    final_price: int


class GlobalComputation(BaseModel):
    kind: Literal[ComputationKind.GLOBAL] = ComputationKind.GLOBAL
    bubble: int
    usd_price: int
    without_bubble: int
    final_price: int


Computation = Annotated[
    SupplierComputation | GlobalComputation,
    Field(discriminator="kind"),
]


class PriceResult(BaseModel):
    buy_price: int
    sell_price: int
    price: int
    buy_spread_rial: int
    sell_spread_rial: int
    buy_spread_rate: Decimal
    sell_spread_rate: Decimal
    priced_at: datetime
    computation: Computation | None = None


class AssetPriceResult(PriceResult):
    asset_id: int


class SourcePriceResult(AssetPriceResult):
    source_id: int

    @classmethod
    def from_sides(
        cls,
        source_id: int,
        asset_id: int,
        selling: int,
        buying: int,
        computation: Computation | None = None,
    ) -> Self:
        price = round((selling + buying) / 2)
        sell_spread = selling - price
        buy_spread = price - buying
        divisor = Decimal(price) if price else Decimal(1)
        result = cls(
            source_id=source_id,
            asset_id=asset_id,
            sell_price=selling,
            buy_price=buying,
            price=price,
            sell_spread_rial=sell_spread,
            buy_spread_rial=buy_spread,
            sell_spread_rate=Decimal(sell_spread) / divisor,
            buy_spread_rate=Decimal(buy_spread) / divisor,
            priced_at=date_utils.utc_now(),
            computation=computation,
        )
        return result


class BubbleResult(BaseModel):
    asset_id: int
    amount: int
    priced_at: datetime


class PriceWindowResult(BaseModel):
    open: int
    high: int
    low: int
    close: int
    bucket: datetime


class AssetPriceWindowResult(PriceWindowResult):
    asset_id: int


class SourcePriceWindowResult(AssetPriceWindowResult):
    source_id: int
