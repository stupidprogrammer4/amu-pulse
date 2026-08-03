from dishka import Provider, Scope, provide

from src.modules.chart.ticker.app.services import (
    PriceSnapshotService,
    PriceTickerService,
    SourcePriceSnapshotService,
    SourcePriceTickerService,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
)
from src.modules.chart.ticker.interfaces import (
    IPriceSnapshotService,
    IPriceTickerService,
    ISourcePriceSnapshotService,
    ISourcePriceTickerService,
)


class TickerProvider(Provider):
    scope = Scope.REQUEST

    price_ticker_repo = provide(PriceTickerRepository)
    source_price_ticker_repo = provide(SourcePriceTickerRepository)
    price_ticker_service = provide(
        PriceTickerService, provides=IPriceTickerService
    )
    source_price_ticker_service = provide(
        SourcePriceTickerService, provides=ISourcePriceTickerService
    )
    price_snapshot_service = provide(
        PriceSnapshotService, provides=IPriceSnapshotService
    )
    source_price_snapshot_service = provide(
        SourcePriceSnapshotService, provides=ISourcePriceSnapshotService
    )
