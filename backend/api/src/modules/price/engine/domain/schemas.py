from datetime import datetime

from src.common.bases.schemas import BaseOutput
from src.modules.price.assets.config.constants import AssetIDField
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.sources.config.constants import SourceIDField
from src.modules.price.symbols.config.constants import SymbolIDField
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode


class PublicPriceOut(BaseOutput):
    # the quote a visitor is shown. Spreads, fees and the reason a source won
    # the selection are an operator's concern and stay off this shape.
    symbol_id: SymbolIDField
    source_id: SourceIDField
    currency: CurrencyType
    buy_price: int
    sell_price: int
    price: int
    priced_at: datetime


class PublicSymbolPricesOut(BaseOutput):
    symbol: SymbolCode
    prices: list[PublicPriceOut]


class PublicBubbleOut(BaseOutput):
    asset_id: AssetIDField
    source_id: SourceIDField
    amount: int
    priced_at: datetime


class PublicAssetBubblesOut(BaseOutput):
    asset: AssetCode
    bubbles: list[PublicBubbleOut]
