from datetime import datetime

from src.common.bases.dtos import BaseDTO
from src.modules.price.symbols.config.constants import SymbolIDInput


class ParamDTO(BaseDTO):
    from_datetime: datetime
    to_datetime: datetime


class SourceParamDTO(ParamDTO):
    symbol_id: SymbolIDInput
