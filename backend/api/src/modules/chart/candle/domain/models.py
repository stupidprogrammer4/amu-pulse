from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declared_attr

from src.infra.postgres.models.base import BaseIDTimestampModel, BaseModel
from src.infra.postgres.types import BigIntField, CharField, ForeignKeyField
from src.modules.chart.candle.domain.enums import TimeFrame


class CandleData(BaseModel):
    timeframe: TimeFrame = CharField(8)

    open: int = BigIntField()
    high: int = BigIntField()
    low: int = BigIntField()
    close: int = BigIntField()

    st_ts: int = BigIntField()
    en_ts: int = BigIntField()


class CandleModel(BaseIDTimestampModel, CandleData, table=True):
    __table_args__ = (UniqueConstraint("asset_id", "timeframe", "st_ts"),)

    asset_id: int = ForeignKeyField("tbl_assets.id", ondelete="CASCADE")


class SourceCandleModel(BaseIDTimestampModel, CandleData, table=True):
    __table_args__ = (
        UniqueConstraint("symbol_id", "source_id", "timeframe", "st_ts"),
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_source_candles"

    symbol_id: int = ForeignKeyField("tbl_symbols.id", ondelete="CASCADE")
    source_id: int = ForeignKeyField("tbl_sources.id", ondelete="CASCADE")
