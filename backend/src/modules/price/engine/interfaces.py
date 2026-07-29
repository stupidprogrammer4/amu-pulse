from typing import Protocol

from src.modules.price.engine.domain.context import CFGContext
from src.modules.price.engine.domain.quotes import SourceQuote


class IPricingEngineService(Protocol):
    # ---------- crawl all sources and save their prices ----------
    async def _fetch_all_db(self) -> CFGContext: ...

    async def _fetch_all_http(self, context: CFGContext) -> SourceQuote: ...

    async def _save_all(
        self, context: CFGContext, quote: SourceQuote
    ) -> int: ...

    async def run(self) -> int: ...


class IPriceCalculatorService(Protocol):
    # ---------- use cached prices in redis to calculate final price ----------
    async def calculate_all(self) -> bool: ...

    async def calculate(self, asset_id: int) -> bool: ...
