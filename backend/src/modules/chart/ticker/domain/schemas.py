from src.common.bases.schemas import BaseMeta, BaseOutput
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.price.assets.config.constants import AssetIDField
from src.modules.price.sources.domain.enums import SourceCode


class PointOutput(BaseOutput):
    price: int
    timestamp: int


class AssetPointOutput(PointOutput):
    asset_id: AssetIDField


class BaseChartOutput(BaseOutput):
    type: ChartType
    points: list[PointOutput]
    from_timestamp: int
    to_timestamp: int


class SourceChartOutput(BaseChartOutput):
    source_points: dict[SourceCode, list[PointOutput]]


class ChartOutput(BaseChartOutput):
    points: list[PointOutput]
    max: int
    min: int
    mean: int
    change_rate: float


class MetaOutput(BaseOutput):
    id: int
    code: str
    title: str
    primary_color: str


class SourceChartMeta(BaseMeta):
    sources: list[MetaOutput]
    symbols: list[MetaOutput]


class ChartMeta(BaseMeta):
    assets: list[MetaOutput]
