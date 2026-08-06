from dishka import Provider, Scope, provide

from src.modules.chart.candle.app.services import (
    CandleService,
    SourceCandleService,
    SourceWindowService,
    WindowService,
)
from src.modules.chart.candle.infra.cache import (
    AssetWindowCache,
    SourceWindowCache,
)
from src.modules.chart.candle.infra.repository import (
    CandleRepository,
    SourceCandleRepository,
)
from src.modules.chart.candle.interfaces import (
    ICandleService,
    ISourceCandleService,
    ISourceWindowService,
    IWindowService,
)


class CandleProvider(Provider):
    scope = Scope.REQUEST

    asset_window_cache = provide(AssetWindowCache, scope=Scope.APP)
    source_window_cache = provide(SourceWindowCache, scope=Scope.APP)
    candle_repo = provide(CandleRepository)
    source_candle_repo = provide(SourceCandleRepository)
    window_service = provide(
        WindowService, provides=IWindowService, scope=Scope.APP
    )
    source_window_service = provide(
        SourceWindowService, provides=ISourceWindowService, scope=Scope.APP
    )
    candle_service = provide(CandleService, provides=ICandleService)
    source_candle_service = provide(
        SourceCandleService, provides=ISourceCandleService
    )
