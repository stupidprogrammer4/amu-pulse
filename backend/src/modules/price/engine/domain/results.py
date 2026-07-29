from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


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

class SourcePriceResult(AssetPriceResult):
    source_id: int
