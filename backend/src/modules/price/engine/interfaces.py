from typing import Protocol, Sequence

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.context import CFGContext
from src.modules.price.engine.domain.quotes import SourceQuote
from src.modules.price.engine.domain.results import (
    SourceBubbleResult,
    SourcePriceResult,
)
from src.modules.price.symbols.domain.enums import SymbolCode


class ICFGReaderService(Protocol):
    async def read_context(self) -> CFGContext: ...


class ICrawlerService(Protocol):
    async def crawl(
        self, cfg: CFGContext
    ) -> tuple[SourceQuote, SourceQuote]: ...


class ICacheFlusherService(Protocol):
    async def flush_results(
        self, cfg: CFGContext, quotes: SourceQuote
    ) -> int: ...


class IPersistFlusherService(Protocol):
    async def flush_errors(
        self,
        cfg: CFGContext,
        quotes: SourceQuote,
    ) -> int: ...


class IRunnerService(Protocol):
    async def run(self) -> bool: ...


class ICacheReaderService(Protocol):
    async def get_by_symbol(
        self, symbol: SymbolCode
    ) -> Sequence[SourcePriceResult]: ...

    async def get_many_by_symbols(
        self, symbols: Sequence[SymbolCode]
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]: ...

    async def get_all(
        self,
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]: ...

    async def get_bubbles_by_asset(
        self, code: AssetCode
    ) -> Sequence[SourceBubbleResult]: ...

    async def get_all_bubbles(
        self,
    ) -> dict[AssetCode, Sequence[SourceBubbleResult]]: ...
