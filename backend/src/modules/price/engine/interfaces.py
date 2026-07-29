from typing import Protocol

from src.modules.price.engine.domain.context import ALLCFGContext, CFGContext
from src.modules.price.engine.domain.quotes import SourceQuote


class IPricingEngineService(Protocol):
    # ---------- all assets ----------
    async def _fetch_all_db(self) -> ALLCFGContext: ...

    async def _fetch_all_http(
        self,
        context: ALLCFGContext
    ) -> SourceQuote: ...

    async def _save_all(
        self,
        context: ALLCFGContext,
        quote: SourceQuote
    ) -> int: ...

    async def run_all(self) -> int: ...

    # ---------- single asset ----------
    async def _fetch_db(
        self,
        asset_id: int
    ) -> CFGContext: ...

    async def _fetch_http(
        self,
        context: CFGContext
    ) -> SourceQuote: ...

    async def _save(
        self,
        context: CFGContext,
        quote: SourceQuote
    ) -> bool: ...

    async def run(
        self,
        asset_id: int
    ) -> bool: ...

