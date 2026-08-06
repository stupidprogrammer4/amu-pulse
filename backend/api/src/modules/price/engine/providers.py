from dishka import Provider, Scope, provide

from src.modules.price.engine.app.services import (
    CacheFlusherService,
    CacheReaderService,
    CFGReaderService,
    CrawlerService,
    PersistFlusherService,
    RunnerService,
)
from src.modules.price.engine.infra.cache import (
    BubbleSourceCache,
    SourcePriceCache,
)
from src.modules.price.engine.infra.readers import (
    AssetReader,
    SourceReader,
    SymbolReader,
)
from src.modules.price.engine.interfaces import (
    ICacheFlusherService,
    ICacheReaderService,
    ICFGReaderService,
    ICrawlerService,
    IPersistFlusherService,
    IRunnerService,
)


class EngineProvider(Provider):
    source_price_cache = provide(SourcePriceCache, scope=Scope.APP)
    bubble_source_cache = provide(BubbleSourceCache, scope=Scope.APP)
    crawler_service = provide(
        CrawlerService, provides=ICrawlerService, scope=Scope.APP
    )
    cache_flusher_service = provide(
        CacheFlusherService, provides=ICacheFlusherService, scope=Scope.APP
    )
    cache_reader_service = provide(
        CacheReaderService, provides=ICacheReaderService, scope=Scope.APP
    )
    runner_service = provide(
        RunnerService, provides=IRunnerService, scope=Scope.APP
    )

    asset_reader = provide(AssetReader, scope=Scope.REQUEST)
    source_reader = provide(SourceReader, scope=Scope.REQUEST)
    symbol_reader = provide(SymbolReader, scope=Scope.REQUEST)
    cfg_reader_service = provide(
        CFGReaderService, provides=ICFGReaderService, scope=Scope.REQUEST
    )
    persist_flusher_service = provide(
        PersistFlusherService,
        provides=IPersistFlusherService,
        scope=Scope.REQUEST,
    )
