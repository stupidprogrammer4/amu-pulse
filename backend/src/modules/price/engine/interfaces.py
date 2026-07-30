from typing import Protocol

from src.modules.price.engine.domain.context import CFGContext
from src.modules.price.engine.domain.quotes import SourceQuote


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
