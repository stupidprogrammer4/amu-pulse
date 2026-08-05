from src.infra.postgres.models.base import BaseIDTimestampModel
from src.infra.postgres.types import CharField, ForeignKeyField, TextField
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode


class SymbolModel(BaseIDTimestampModel, table=True):
    title: str = CharField(55)
    code: SymbolCode = CharField(55, unique=True)
    asset_id: int = ForeignKeyField("tbl_assets.id", ondelete="CASCADE")
    currency: CurrencyType = CharField(16)
    description: str | None = TextField(nullable=True)
    primary_color: str = CharField(55)
