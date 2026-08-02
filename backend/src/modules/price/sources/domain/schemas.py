from datetime import datetime

from pydantic import Field, computed_field

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.price.sources.config.constants import (
    SOURCE_ID_ENCRYPTION,
    SourceIDField,
)
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.errors import SourceErrorInfo
from src.modules.price.symbols.config.constants import SymbolIDField
from src.modules.price.symbols.domain.enums import (
    CurrencyType,
    SymbolCode,
)


class SourceConfigOut(BaseOutput):
    source_id: SourceIDField
    timeout: int
    # write-only: carried for the flags below, dropped from the output
    headers_credentials: dict[str, str] | None = Field(
        default=None, exclude=True
    )
    auth_credentials: dict[str, str] | None = Field(default=None, exclude=True)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def has_headers_credentials(self) -> bool:
        return self.headers_credentials is not None

    @computed_field
    @property
    def has_auth_credentials(self) -> bool:
        return self.auth_credentials is not None


class SourceOut(BaseIDOutput):
    __encryption__ = SOURCE_ID_ENCRYPTION

    title: str
    code: SourceCode
    website_url: str
    icon_url: str
    primary_color: str
    source_type: SourceSwitch
    error: SourceErrorInfo | None
    created_at: datetime
    updated_at: datetime


class SourceWithConfigOut(SourceOut):
    config: SourceConfigOut | None = None


class SourcePriceOut(BaseOutput):
    source_id: SourceIDField
    symbol_id: SymbolIDField
    currency: CurrencyType
    buy_price: int
    sell_price: int
    price: int
    buy_spread: int
    sell_spread: int
    buy_spread_rate: float
    sell_spread_rate: float
    priced_at: datetime


class SymbolPricesOut(BaseOutput):
    symbol: SymbolCode
    prices: list[SourcePriceOut]
