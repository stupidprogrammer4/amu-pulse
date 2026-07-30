from datetime import datetime

from src.common.bases.schemas import BaseIDOutput
from src.modules.price.assets.config.constants import AssetIDField
from src.modules.price.symbols.config.constants import SYMBOL_ID_ENCRYPTION
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode


class SymbolOut(BaseIDOutput):
    __encryption__ = SYMBOL_ID_ENCRYPTION

    title: str
    code: SymbolCode
    asset_id: AssetIDField
    currency: CurrencyType
    description: str | None
    created_at: datetime
    updated_at: datetime
