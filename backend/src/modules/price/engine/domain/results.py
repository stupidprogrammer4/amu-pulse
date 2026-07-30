from datetime import datetime

from pydantic import BaseModel

from src.modules.price.engine.domain.enums import SelectionReason
from src.modules.price.symbols.domain.enums import CurrencyType


class PriceResult(BaseModel):
    buy_price: int
    sell_price: int
    price: int
    buy_spread: int
    sell_spread: int
    buy_spread_rate: float
    sell_spread_rate: float
    priced_at: datetime


class FeeResult(BaseModel):
    buy_fee_rate: float
    sell_fee_rate: float
    buy_fee_rial: int
    sell_fee_rial: int


class SourcePriceResult(PriceResult):
    symbol_id: int
    source_id: int
    currency: CurrencyType
    is_selected: bool = False
    fee: FeeResult | None = None
    reason: SelectionReason | None = None


class SourceBubbleResult(BaseModel):
    asset_id: int
    source_id: int
    amount: int
    priced_at: datetime
