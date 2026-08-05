from types import SimpleNamespace
from typing import cast

from src.infra.redis.client import RedisClient
from src.modules.chart.candle.domain.windows import (
    AssetPriceWindow,
    SourcePriceWindow,
)
from src.modules.chart.candle.infra.cache import (
    AssetWindowCache,
    SourceWindowCache,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.symbols.domain.enums import SymbolCode
from tests.unit.calculator.test_asset_price_cache import _FakeRedis

_st_ts = 1_785_000_000


class _FakeWindowRedis(_FakeRedis):
    """The fake, plus the expiry the window caches set."""

    def __init__(self) -> None:
        super().__init__()
        self.expiries: dict[str, int] = {}

    async def expire(self, name: str, seconds: int) -> int:
        self.expiries[name] = seconds
        return 1


def _assets() -> tuple[AssetWindowCache, _FakeWindowRedis]:
    """
    Desc: Build the asset window cache over a fake Redis.
    Returns:
        return (tuple[AssetWindowCache, _FakeWindowRedis]): The cache and
            its store.
    """
    fake = _FakeWindowRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    return AssetWindowCache(client), fake


def _sources() -> tuple[SourceWindowCache, _FakeWindowRedis]:
    """
    Desc: Build the source window cache over a fake Redis.
    Returns:
        return (tuple[SourceWindowCache, _FakeWindowRedis]): The cache and
            its store.
    """
    fake = _FakeWindowRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    return SourceWindowCache(client), fake


class TestTheAssetWindow:
    async def test_a_window_round_trips(self) -> None:
        cache, _ = _assets()
        window = AssetPriceWindow.opened(1, 100).folded(140).folded(110)

        await cache.set(_st_ts, AssetCode.GOLD18, window)
        found = await cache.get(_st_ts, AssetCode.GOLD18)

        assert found is not None
        assert (found.open, found.high, found.low, found.close) == (
            100,
            140,
            100,
            110,
        )
        assert found.asset_id == 1

    async def test_each_window_is_a_hash_of_its_own(self) -> None:
        cache, fake = _assets()
        window = AssetPriceWindow.opened(1, 100)

        await cache.set(_st_ts, AssetCode.GOLD18, window)
        await cache.set(_st_ts + 300, AssetCode.GOLD18, window)

        assert set(fake.store) == {
            f"assets:window:{_st_ts}",
            f"assets:window:{_st_ts + 300}",
        }

    async def test_a_window_nobody_flushed_expires(self) -> None:
        cache, fake = _assets()

        await cache.set(
            _st_ts, AssetCode.GOLD18, AssetPriceWindow.opened(1, 1)
        )

        assert fake.expiries[f"assets:window:{_st_ts}"] == cache.ttl

    async def test_the_whole_window_comes_back_at_once(self) -> None:
        cache, _ = _assets()
        await cache.set_many(
            _st_ts,
            {
                AssetCode.GOLD18: AssetPriceWindow.opened(1, 100),
                AssetCode.USD: AssetPriceWindow.opened(2, 1_900),
            },
        )

        found = await cache.get_all(_st_ts)

        assert {code: row.open for code, row in found.items()} == {
            AssetCode.GOLD18: 100,
            AssetCode.USD: 1_900,
        }

    async def test_only_the_assets_asked_for_come_back(self) -> None:
        cache, _ = _assets()
        await cache.set_many(
            _st_ts,
            {
                AssetCode.GOLD18: AssetPriceWindow.opened(1, 100),
                AssetCode.USD: AssetPriceWindow.opened(2, 1_900),
            },
        )

        found = await cache.get_many(_st_ts, [AssetCode.USD])

        assert list(found) == [AssetCode.USD]

    async def test_a_window_nobody_wrote_reads_empty(self) -> None:
        cache, _ = _assets()

        assert await cache.get(_st_ts, AssetCode.GOLD18) is None
        assert await cache.get_all(_st_ts) == {}

    async def test_the_flusher_drops_the_window_it_wrote_down(self) -> None:
        cache, _ = _assets()
        await cache.set(
            _st_ts, AssetCode.GOLD18, AssetPriceWindow.opened(1, 1)
        )

        await cache.remove(_st_ts)

        assert await cache.get_all(_st_ts) == {}


class TestTheSourceWindow:
    async def test_every_source_of_a_line_round_trips(self) -> None:
        cache, _ = _sources()
        await cache.set(
            _st_ts,
            SymbolCode.GOLD18_GRAM,
            [
                SourcePriceWindow.opened(12, 1, 100).folded(120),
                SourcePriceWindow.opened(13, 1, 101),
            ],
        )

        found = await cache.get(_st_ts, SymbolCode.GOLD18_GRAM)

        assert [row.source_id for row in found] == [12, 13]
        assert (found[0].high, found[0].close) == (120, 120)

    async def test_each_line_keeps_its_own_field(self) -> None:
        cache, _ = _sources()
        await cache.set_many(
            _st_ts,
            {
                SymbolCode.GOLD18_GRAM: [SourcePriceWindow.opened(12, 1, 100)],
                SymbolCode.USD_RIAL: [SourcePriceWindow.opened(12, 2, 1_900)],
            },
        )

        found = await cache.get_all(_st_ts)

        assert {code: rows[0].open for code, rows in found.items()} == {
            SymbolCode.GOLD18_GRAM: 100,
            SymbolCode.USD_RIAL: 1_900,
        }

    async def test_only_the_lines_asked_for_come_back(self) -> None:
        cache, _ = _sources()
        await cache.set_many(
            _st_ts,
            {
                SymbolCode.GOLD18_GRAM: [SourcePriceWindow.opened(12, 1, 100)],
                SymbolCode.USD_RIAL: [SourcePriceWindow.opened(12, 2, 1_900)],
            },
        )

        found = await cache.get_many(_st_ts, [SymbolCode.USD_RIAL])

        assert list(found) == [SymbolCode.USD_RIAL]

    async def test_a_line_nobody_quoted_reads_empty(self) -> None:
        cache, _ = _sources()

        assert await cache.get(_st_ts, SymbolCode.GOLD18_GRAM) == []
        assert await cache.get_all(_st_ts) == {}

    async def test_the_flusher_drops_the_window_it_wrote_down(self) -> None:
        cache, _ = _sources()
        await cache.set(
            _st_ts,
            SymbolCode.GOLD18_GRAM,
            [SourcePriceWindow.opened(12, 1, 100)],
        )

        await cache.remove(_st_ts)

        assert await cache.get_all(_st_ts) == {}


class TestFoldingAPrice:
    def test_the_first_price_opens_a_flat_window(self) -> None:
        window = AssetPriceWindow.opened(1, 100)

        assert (window.open, window.high, window.low, window.close) == (
            100,
            100,
            100,
            100,
        )

    def test_a_higher_price_lifts_only_the_high_and_the_close(self) -> None:
        window = AssetPriceWindow.opened(1, 100).folded(140)

        assert (window.open, window.high, window.low, window.close) == (
            100,
            140,
            100,
            140,
        )

    def test_a_lower_price_drops_only_the_low_and_the_close(self) -> None:
        window = AssetPriceWindow.opened(1, 100).folded(90)

        assert (window.high, window.low, window.close) == (100, 90, 90)

    def test_the_open_never_moves(self) -> None:
        window = AssetPriceWindow.opened(1, 100)

        for price in (140, 90, 110):
            window = window.folded(price)

        assert window.open == 100
        assert window.close == 110
