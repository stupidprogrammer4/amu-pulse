from dataclasses import dataclass
from decimal import Decimal
from typing import Self, Sequence

from src.common.utils import currency_utils
from src.common.utils.currency_utils import QuotedAmount
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.enums import GlobalSymbol, QuoteKind
from src.modules.price.sources.domain.enums import ErrorType, SourceCode


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
    # the fetcher names the metal, so nothing downstream assumes it
    code: SourceCode
    asset: AssetCode
    kind: QuoteKind
    selling: int
    buying: int
    is_closed: bool = False
    error: ErrorQuote | None = None

    @classmethod
    def from_pair(
        cls,
        code: SourceCode,
        asset: AssetCode,
        kind: QuoteKind,
        first: QuotedAmount,
        second: QuotedAmount,
        is_closed: bool = False,
    ) -> Self:
        # sources quote numbers as strings; compare them as Rial, not text
        first_rial = currency_utils.to_rial(first)
        second_rial = currency_utils.to_rial(second)
        quote = cls(
            code=code,
            asset=asset,
            kind=kind,
            selling=max(first_rial, second_rial),
            buying=min(first_rial, second_rial),
            is_closed=is_closed,
        )
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        asset: AssetCode,
        kind: QuoteKind,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(
            code=code, asset=asset, kind=kind, selling=0, buying=0, error=error
        )
        return quote


@dataclass(frozen=True, slots=True)
class IranSourceQuote:
    # an Iranian market feed: rial prices, one row per asset it quotes
    code: SourceCode
    asset: AssetCode
    selling: int
    buying: int
    error: ErrorQuote | None = None

    @classmethod
    def from_pair(
        cls,
        code: SourceCode,
        asset: AssetCode,
        first: QuotedAmount,
        second: QuotedAmount,
    ) -> Self:
        first_rial = currency_utils.to_rial(first)
        second_rial = currency_utils.to_rial(second)
        quote = cls(
            code=code,
            asset=asset,
            selling=max(first_rial, second_rial),
            buying=min(first_rial, second_rial),
        )
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        asset: AssetCode,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(code=code, asset=asset, selling=0, buying=0, error=error)
        return quote


@dataclass(frozen=True, slots=True)
class GlobalSourceQuote:
    # a world feed: priced in USD, so Decimal rather than integer Rial
    code: SourceCode
    symbol: GlobalSymbol
    selling: Decimal
    buying: Decimal
    error: ErrorQuote | None = None

    @classmethod
    def from_pair(
        cls,
        code: SourceCode,
        symbol: GlobalSymbol,
        first: QuotedAmount,
        second: QuotedAmount,
    ) -> Self:
        first_usd = currency_utils.to_decimal(first)
        second_usd = currency_utils.to_decimal(second)
        quote = cls(
            code=code,
            symbol=symbol,
            selling=max(first_usd, second_usd),
            buying=min(first_usd, second_usd),
        )
        return quote

    @classmethod
    def from_mid(
        cls,
        code: SourceCode,
        symbol: GlobalSymbol,
        price: QuotedAmount,
    ) -> Self:
        mid = currency_utils.to_decimal(price)
        quote = cls(code=code, symbol=symbol, selling=mid, buying=mid)
        return quote

    @classmethod
    def failed(
        cls,
        code: SourceCode,
        symbol: GlobalSymbol,
        error: ErrorQuote,
    ) -> Self:
        quote = cls(
            code=code,
            symbol=symbol,
            selling=Decimal(0),
            buying=Decimal(0),
            error=error,
        )
        return quote


@dataclass(frozen=True, slots=True)
class BubbleQuote:
    # a published premium, not a price; negative below world parity
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
