from datetime import datetime

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.price.assets.config.constants import AssetIDField
from src.modules.price.symbols.config.constants import (
    SYMBOL_ID_ENCRYPTION,
    SymbolIDField,
)
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode


class SymbolOut(BaseIDOutput):
    __encryption__ = SYMBOL_ID_ENCRYPTION

    title: str
    code: SymbolCode
    asset_id: AssetIDField
    currency: CurrencyType
    primary_color: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class SymbolMetaOut(BaseOutput):
    id: SymbolIDField
    code: SymbolCode
    title: str
    primary_color: str
