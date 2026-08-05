from sqlalchemy.orm import declared_attr

from src.infra.postgres.models.base import BaseIDTimestampModel
from src.infra.postgres.types import BigIntField, ForeignKeyField


class PriceTickerModel(BaseIDTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_price_tickers"

    asset_id: int = ForeignKeyField("tbl_assets.id", ondelete="CASCADE")
    price: int = BigIntField()
    timestamp: int = BigIntField()


class SourcePriceTickerModel(BaseIDTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_source_price_tickers"

    symbol_id: int = ForeignKeyField("tbl_symbols.id", ondelete="CASCADE")
    source_id: int = ForeignKeyField("tbl_sources.id", ondelete="CASCADE")

    price: int = BigIntField()
    timestamp: int = BigIntField()
