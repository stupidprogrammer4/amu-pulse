from dataclasses import dataclass
from typing import Self, Sequence

from src.common.utils import currency_utils
from src.common.utils.currency_utils import QuotedAmount
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.sources.domain.enums import ErrorType, SourceCode
from src.modules.price.symbols.domain.enums import SymbolCode


@dataclass(frozen=True, slots=True)
class HTTPErrorQuote:
    raw_content: str
    status_code: str
    json: dict[str, str] | None


@dataclass(frozen=True, slots=True)
class ErrorQuote:
    error_type: ErrorType
    message: str
    http_error: HTTPErrorQuote | None = None


@dataclass(frozen=True, slots=True)
class SupplierSourceQuote:
    # the fetcher names the line, so nothing downstream assumes it
    code: SourceCode
    symbol: SymbolCode
    selling_mazane: int
    buying_mazane: int
    is_closed: bool = False
    error: ErrorQuote | None = None

    @classmethod
    def from_pair(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        first: QuotedAmount,
        second: QuotedAmount,
        is_closed: bool = False,
    ) -> Self:
        # sources quote numbers as strings; compare them as Rial, not text
        first_rial = currency_utils.to_rial(first)
        second_rial = currency_utils.to_rial(second)
        quote = cls(
            code=code,
            symbol=symbol,
            selling_mazane=currency_utils.round_rial(
                max(first_rial, second_rial)
            ),
            buying_mazane=currency_utils.round_rial(
                min(first_rial, second_rial)
            ),
            is_closed=is_closed,
        )
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(
            code=code,
            symbol=symbol,
            selling_mazane=0,
            buying_mazane=0,
            error=error,
        )
        return quote


@dataclass(frozen=True, slots=True)
class FeeQuote:
    sell_rate: float
    buy_rate: float


@dataclass(frozen=True, slots=True)
class IranSourceQuote:
    # an Iranian market feed: rial prices, one row per line it quotes
    code: SourceCode
    symbol: SymbolCode
    price_rial: int
    buy_fee_rial: int
    sell_fee_rial: int
    buy_price_rial: int
    sell_price_rial: int
    fee: FeeQuote | None = None

    error: ErrorQuote | None = None

    @classmethod
    def from_price_and_fee(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        price_rial: QuotedAmount,
        fee: FeeQuote,
    ) -> Self:
        # one mid price, with the fee opening the spread around it
        price = currency_utils.round_rial(currency_utils.to_rial(price_rial))
        buy_fee = round(price * fee.buy_rate)
        sell_fee = round(price * fee.sell_rate)
        quote = cls(
            code=code,
            symbol=symbol,
            price_rial=price,
            buy_fee_rial=buy_fee,
            sell_fee_rial=sell_fee,
            buy_price_rial=currency_utils.round_rial(price - buy_fee),
            sell_price_rial=currency_utils.round_rial(price + sell_fee),
            fee=fee,
        )
        return quote

    @classmethod
    def from_buying_selling(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        first: QuotedAmount,
        second: QuotedAmount,
        fee: FeeQuote | None = None,
    ) -> Self:
        # sources quote numbers as strings; compare them as Rial, not text
        first_rial = currency_utils.to_rial(first)
        second_rial = currency_utils.to_rial(second)
        buying = min(first_rial, second_rial)
        selling = max(first_rial, second_rial)
        buy_fee = 0
        sell_fee = 0
        if fee is not None:
            buy_fee = round(buying * fee.buy_rate)
            sell_fee = round(selling * fee.sell_rate)
        quote = cls(
            code=code,
            symbol=symbol,
            price_rial=currency_utils.round_rial((buying + selling) / 2),
            buy_fee_rial=buy_fee,
            sell_fee_rial=sell_fee,
            buy_price_rial=currency_utils.round_rial(buying - buy_fee),
            sell_price_rial=currency_utils.round_rial(selling + sell_fee),
            fee=fee,
        )
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(
            code=code,
            symbol=symbol,
            price_rial=0,
            buy_fee_rial=0,
            sell_fee_rial=0,
            buy_price_rial=0,
            sell_price_rial=0,
            error=error,
        )
        return quote


@dataclass(frozen=True, slots=True)
class GlobalSourceQuote:
    # a world feed prices in dollars, so its unit is the cent
    code: SourceCode
    symbol: SymbolCode
    selling_cent: int
    buying_cent: int
    error: ErrorQuote | None = None

    @classmethod
    def from_pair(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        first: QuotedAmount,
        second: QuotedAmount,
    ) -> Self:
        first_cent = currency_utils.to_cent(first)
        second_cent = currency_utils.to_cent(second)
        quote = cls(
            code=code,
            symbol=symbol,
            selling_cent=max(first_cent, second_cent),
            buying_cent=min(first_cent, second_cent),
        )
        return quote

    @classmethod
    def from_mid(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        price: QuotedAmount,
    ) -> Self:
        mid = currency_utils.to_cent(price)
        quote = cls(
            code=code, symbol=symbol, selling_cent=mid, buying_cent=mid
        )
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        symbol: SymbolCode,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(
            code=code,
            symbol=symbol,
            selling_cent=0,
            buying_cent=0,
            error=error,
        )
        return quote


@dataclass(frozen=True, slots=True)
class BubbleQuote:
    # a published premium of a whole asset, not of one quoted line
    code: SourceCode
    asset: AssetCode
    amount: int
    error: ErrorQuote | None = None

    @classmethod
    def from_amount(
        cls,
        code: SourceCode,
        asset: AssetCode,
        amount: QuotedAmount,
    ) -> Self:
        quote = cls(
            code=code,
            asset=asset,
            amount=currency_utils.to_rial(amount),
        )
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        asset: AssetCode,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(code=code, asset=asset, amount=0, error=error)
        return quote


@dataclass(frozen=True, slots=True)
class SourceQuote:
    irans: Sequence[IranSourceQuote]
    globals: Sequence[GlobalSourceQuote]
    suppliers: Sequence[SupplierSourceQuote]
    bubbles: Sequence[BubbleQuote]
