from src.common.bases.schemas import BaseMeta, BaseOutput
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.price.assets.config.constants import AssetIDField
from src.modules.price.sources.config.constants import SourceIDField
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.symbols.config.constants import SymbolIDField


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


class BaseMetaOutput(BaseOutput):
    code: str
    title: str
    primary_color: str


class SourceMetaOutput(BaseMetaOutput):
    id: SourceIDField

class SymbolMetaOutput(BaseMetaOutput):
    id: SymbolIDField

class AssetMetaOutput(BaseMetaOutput):
    id: AssetIDField

class SourceChartMeta(BaseMeta):
    sources: list[SourceMetaOutput]
    symbols: list[SymbolMetaOutput]


class ChartMeta(BaseMeta):
    assets: list[AssetMetaOutput]
