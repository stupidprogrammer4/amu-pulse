from src.common.bases.dtos import BaseDTO
from src.common.types import ContentType, StrType
from src.modules.price.assets.config.constants import AssetIDInput
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode


class SymbolCreate(BaseDTO):
    title: StrType
    code: SymbolCode
    asset_id: AssetIDInput
    currency: CurrencyType
    description: ContentType | None = None


class SymbolUpdate(BaseDTO):
    title: StrType | None = None
    currency: CurrencyType | None = None
    description: ContentType | None = None
