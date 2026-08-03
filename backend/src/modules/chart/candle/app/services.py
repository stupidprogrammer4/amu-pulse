from typing import Mapping, Sequence

from src.modules.chart.candle.app.helpers import WindowClock
from src.modules.chart.candle.domain.windows import (
    AssetPriceWindow,
    SourcePriceWindow,
)
from src.modules.chart.candle.infra.cache import (
    AssetWindowCache,
    SourceWindowCache,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.symbols.domain.enums import SymbolCode


class WindowService:
    def __init__(self, cache: AssetWindowCache) -> None:
        """
        Desc: Build the service with the window each price is folded into.
        Args:
            cache (AssetWindowCache): Where the open window lives.
        """
        self.cache = cache
        self.clock = WindowClock()

    def _folded(
        self,
        standing: AssetPriceWindow | None,
        priced: AssetPriceResult,
    ) -> AssetPriceWindow:
        """
        Desc: Take a price into the open window, opening one when it is the
        first price of that window.
        Args:
            standing (AssetPriceWindow | None): The window as it stands, or
                None when nothing has been folded into it yet.
            priced (AssetPriceResult): What the asset was last priced at.
        Returns:
            return (AssetPriceWindow): The window with that price in it.
        """
        window = AssetPriceWindow.opened(priced.asset_id, priced.price)
        if standing is not None:
            window = standing.folded(priced.price)
        return window

    async def update_window(
        self,
        code: AssetCode,
        cached_prices: AssetPriceResult,
    ) -> bool:
        """
        Desc: Fold what one asset is priced at into the open window.
        Args:
            code (AssetCode): The asset that was priced.
            cached_prices (AssetPriceResult): What it was priced at.
        Returns:
            return (bool): Whether the price was folded in.
        """
        opened = self.clock.opened_now()
        standing = await self.cache.get(opened, code)
        window = self._folded(standing, cached_prices)
        await self.cache.set(opened, code, window)
        return True

    async def update_windows(
        self,
        cached_prices: dict[AssetCode, AssetPriceResult],
    ) -> int:
        """
        Desc: Fold what every asset is priced at into the open window.
        Args:
            cached_prices (dict[AssetCode, AssetPriceResult]): What each
                asset was priced at.
        Returns:
            return (int): How many prices were folded in.
        """
        opened = self.clock.opened_now()
        folded: dict[AssetCode, AssetPriceWindow] = {}
        if cached_prices:
            standing = await self.cache.get_many(opened, list(cached_prices))
            folded = {
                code: self._folded(standing.get(code), price)
                for code, price in cached_prices.items()
            }
            await self.cache.set_many(opened, folded)
        return len(folded)


class SourceWindowService:
    def __init__(self, cache: SourceWindowCache) -> None:
        """
        Desc: Build the service with the window each reading is folded
        into.
        Args:
            cache (SourceWindowCache): Where the open window lives.
        """
        self.cache = cache
        self.clock = WindowClock()

    def _folded(
        self,
        standing: Sequence[SourcePriceWindow],
        quoted: Sequence[SourcePriceResult],
    ) -> list[SourcePriceWindow]:
        """
        Desc: Take a line's readings into the open window, one window per
        source that quoted it.
        Args:
            standing (Sequence[SourcePriceWindow]): The line's windows as
                they stand, empty when nothing has been folded in yet.
            quoted (Sequence[SourcePriceResult]): What each source quoted
                that line at.
        Returns:
            return (list[SourcePriceWindow]): The line's windows with those
                readings in them.
        """
        windows = {window.source_id: window for window in standing}
        for row in quoted:
            # a window opened on the reading folds it back as a no-op, so
            # the first reading of a source needs no branch of its own
            window = windows.get(
                row.source_id,
                SourcePriceWindow.opened(
                    row.source_id, row.symbol_id, row.price
                ),
            )
            windows[row.source_id] = window.folded(row.price)
        return list(windows.values())

    async def update_window(
        self,
        cached_prices: Mapping[SymbolCode, Sequence[SourcePriceResult]],
    ) -> int:
        """
        Desc: Fold what every source quoted into the open window, line by
        line.
        Args:
            cached_prices (Mapping[SymbolCode, Sequence[SourcePriceResult]]):
                What each line was quoted at, by every source quoting it.
        Returns:
            return (int): How many readings were folded in.
        """
        opened = self.clock.opened_now()
        folded = 0
        if cached_prices:
            standing = await self.cache.get_many(opened, list(cached_prices))
            windows = {
                code: self._folded(standing.get(code, ()), quoted)
                for code, quoted in cached_prices.items()
            }
            await self.cache.set_many(opened, windows)
            folded = sum(len(quoted) for quoted in cached_prices.values())
        return folded
