from datetime import datetime
from types import SimpleNamespace
from typing import cast

from src.common.utils import date_utils
from src.infra.redis.client import RedisClient
from src.modules.chart.candle.app.services import SourceWindowService
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.infra.cache import SourceWindowCache
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from tests.unit.candle.test_window_caches import _FakeWindowRedis


def _service() -> tuple[SourceWindowService, SourceWindowCache]:
    """
    Desc: Build the source window service over a fake Redis.
    Returns:
        return (tuple[SourceWindowService, SourceWindowCache]): The service
            and the cache it folds into.
    """
    fake = _FakeWindowRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    cache = SourceWindowCache(client)
    return SourceWindowService(cache), cache


def _quoted(
    price: int,
    source_id: int = 12,
    symbol_id: int = 1,
    priced_at: datetime | None = None,
) -> SourcePriceResult:
    """
    Desc: Build what a source quoted a line at, now unless told otherwise.
    Args:
        price (int): The mid price in rial.
        source_id (int): ID of the source that quoted it.
        symbol_id (int): ID of the line it was quoted for.
        priced_at (datetime | None): When it was quoted, or now.
    Returns:
        return (SourcePriceResult): The reading.
    """
    return SourcePriceResult(
        symbol_id=symbol_id,
        source_id=source_id,
        currency=CurrencyType.RIAL,
        buy_price=price - 1_000,
        sell_price=price + 1_000,
        price=price,
        buy_spread=1_000,
        sell_spread=1_000,
        buy_spread_rate=0.1,
        sell_spread_rate=0.1,
        priced_at=priced_at or date_utils.utc_now(),
    )


def _opened_now() -> int:
    """
    Desc: Read when the window readings are folded into opened at.
    Returns:
        return (int): The moment it opened, in whole seconds.
    """
    stamp = int(date_utils.utc_now().timestamp())
    return TimeFrame.FIVE_MINUTE.opened_at(stamp)


class TestFoldingWhatEverySourceQuoted:
    async def test_the_first_reading_opens_the_window_flat(self) -> None:
        service, cache = _service()

        folded = await service.update_window(
            {SymbolCode.GOLD18_GRAM: [_quoted(100)]}
        )

        windows = await cache.get(_opened_now(), SymbolCode.GOLD18_GRAM)
        window = windows[0]
        assert folded == 1
        assert (window.open, window.high, window.low, window.close) == (
            100,
            100,
            100,
            100,
        )
        assert (window.source_id, window.symbol_id) == (12, 1)

    async def test_the_next_reading_folds_into_the_standing_window(
        self,
    ) -> None:
        service, cache = _service()

        for price in (100, 140, 90):
            await service.update_window(
                {SymbolCode.GOLD18_GRAM: [_quoted(price)]}
            )

        windows = await cache.get(_opened_now(), SymbolCode.GOLD18_GRAM)
        window = windows[0]
        assert (window.open, window.high, window.low, window.close) == (
            100,
            140,
            90,
            90,
        )

    async def test_each_source_of_a_line_keeps_a_window_of_its_own(
        self,
    ) -> None:
        service, cache = _service()

        folded = await service.update_window(
            {
                SymbolCode.GOLD18_GRAM: [
                    _quoted(100, source_id=12),
                    _quoted(101, source_id=13),
                ]
            }
        )

        windows = await cache.get(_opened_now(), SymbolCode.GOLD18_GRAM)
        assert folded == 2
        assert {row.source_id: row.open for row in windows} == {
            12: 100,
            13: 101,
        }

    async def test_several_readings_of_a_source_fold_into_one_window(
        self,
    ) -> None:
        # one source of one line is written down as one candle, however
        # many readings it was quoted at
        service, cache = _service()

        folded = await service.update_window(
            {
                SymbolCode.GOLD18_GRAM: [
                    _quoted(100),
                    _quoted(140),
                    _quoted(90),
                ]
            }
        )

        windows = await cache.get(_opened_now(), SymbolCode.GOLD18_GRAM)
        assert folded == 3
        assert len(windows) == 1
        assert (
            windows[0].open,
            windows[0].high,
            windows[0].low,
            windows[0].close,
        ) == (100, 140, 90, 90)

    async def test_every_line_is_folded_in_one_go(self) -> None:
        service, cache = _service()

        folded = await service.update_window(
            {
                SymbolCode.GOLD18_GRAM: [_quoted(100, symbol_id=1)],
                SymbolCode.USD_RIAL: [_quoted(1_900, symbol_id=2)],
            }
        )

        windows = await cache.get_all(_opened_now())
        assert folded == 2
        assert {code: rows[0].close for code, rows in windows.items()} == {
            SymbolCode.GOLD18_GRAM: 100,
            SymbolCode.USD_RIAL: 1_900,
        }

    async def test_a_source_that_stopped_quoting_keeps_its_window(
        self,
    ) -> None:
        service, cache = _service()

        await service.update_window(
            {
                SymbolCode.GOLD18_GRAM: [
                    _quoted(100, source_id=12),
                    _quoted(101, source_id=13),
                ]
            }
        )
        await service.update_window(
            {SymbolCode.GOLD18_GRAM: [_quoted(140, source_id=12)]}
        )

        windows = await cache.get(_opened_now(), SymbolCode.GOLD18_GRAM)
        assert {row.source_id: row.close for row in windows} == {
            12: 140,
            13: 101,
        }

    async def test_a_line_the_crawl_left_out_stays_as_it_was(self) -> None:
        service, cache = _service()

        await service.update_window(
            {
                SymbolCode.GOLD18_GRAM: [_quoted(100, symbol_id=1)],
                SymbolCode.USD_RIAL: [_quoted(1_900, symbol_id=2)],
            }
        )
        await service.update_window({SymbolCode.GOLD18_GRAM: [_quoted(140)]})

        windows = await cache.get_all(_opened_now())
        assert {code: rows[0].close for code, rows in windows.items()} == {
            SymbolCode.GOLD18_GRAM: 140,
            SymbolCode.USD_RIAL: 1_900,
        }

    async def test_a_crawl_that_quoted_nothing_folds_nothing(self) -> None:
        service, cache = _service()

        folded = await service.update_window({})

        assert folded == 0
        assert await cache.get_all(_opened_now()) == {}
