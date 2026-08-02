from dishka import Provider, Scope, provide

from src.modules.chart.ticker.app.services import (
    MetaService,
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
    IMetaService,
    IPriceSnapshotService,
    IPriceTickerService,
    ISourcePriceSnapshotService,
    ISourcePriceTickerService,
)


class TickerProvider(Provider):
    scope = Scope.REQUEST

    price_ticker_repo = provide(PriceTickerRepository)
    source_price_ticker_repo = provide(SourcePriceTickerRepository)
    meta_service = provide(MetaService, provides=IMetaService)
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
