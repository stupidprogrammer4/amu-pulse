from types import SimpleNamespace
from typing import Sequence, cast

from src.common.utils import date_utils
from src.infra.redis.client import RedisClient
from src.modules.chart.candle.app.services import (
    CandleService,
    SourceCandleService,
)
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.domain.models import (
    CandleModel,
    SourceCandleModel,
)
from src.modules.chart.candle.domain.windows import (
    AssetPriceWindow,
    SourcePriceWindow,
)
from src.modules.chart.candle.infra.cache import (
    AssetWindowCache,
    SourceWindowCache,
)
from src.modules.chart.candle.infra.repository import (
    CandleRepository,
    SourceCandleRepository,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.symbols.domain.enums import SymbolCode
from tests.unit.candle.test_window_caches import _FakeWindowRedis

_five_minutes = TimeFrame.FIVE_MINUTE.seconds


class _FakeCandleRepo:
    """The candle table, as a dict keyed the way the unique index is."""

    def __init__(self) -> None:
        self.rows: dict[tuple[int, str, int], CandleModel] = {}

    async def bulk_upsert(
        self, candles: Sequence[CandleModel]
    ) -> Sequence[CandleModel]:
        for row in candles:
            self.rows[(row.asset_id, row.timeframe, row.st_ts)] = row
        return list(candles)

    async def get_all_by_timeframe(
        self,
        timeframe: TimeFrame,
        from_ts: int,
        to_ts: int,
    ) -> Sequence[CandleModel]:
        found = [
            row
            for row in self.rows.values()
            if row.timeframe == timeframe and from_ts <= row.st_ts < to_ts
        ]
        return sorted(found, key=lambda row: (row.asset_id, row.st_ts))


class _FakeSourceCandleRepo:
    """The source candle table, keyed the way its unique index is."""

    def __init__(self) -> None:
        self.rows: dict[tuple[int, int, str, int], SourceCandleModel] = {}

    async def bulk_upsert(
        self, candles: Sequence[SourceCandleModel]
    ) -> Sequence[SourceCandleModel]:
        for row in candles:
            key = (row.source_id, row.symbol_id, row.timeframe, row.st_ts)
            self.rows[key] = row
        return list(candles)

    async def get_all_by_timeframe(
        self,
        timeframe: TimeFrame,
        from_ts: int,
        to_ts: int,
    ) -> Sequence[SourceCandleModel]:
        found = [
            row
            for row in self.rows.values()
            if row.timeframe == timeframe and from_ts <= row.st_ts < to_ts
        ]
        return sorted(
            found, key=lambda row: (row.source_id, row.symbol_id, row.st_ts)
        )


def _assets() -> tuple[CandleService, _FakeCandleRepo, AssetWindowCache]:
    """
    Desc: Build the candle service over a fake table and a fake Redis.
    Returns:
        return (tuple[CandleService, _FakeCandleRepo, AssetWindowCache]):
            The service, the table it writes to and the window cache.
    """
    repo = _FakeCandleRepo()
    client = cast(RedisClient, SimpleNamespace(client=_FakeWindowRedis()))
    cache = AssetWindowCache(client)
    service = CandleService(cast(CandleRepository, repo), cache)
    return service, repo, cache


def _sources() -> tuple[
    SourceCandleService, _FakeSourceCandleRepo, SourceWindowCache
]:
    """
    Desc: Build the source candle service over a fake table and Redis.
    Returns:
        return (tuple[SourceCandleService, _FakeSourceCandleRepo,
            SourceWindowCache]): The service, the table it writes to and
            the window cache.
    """
    repo = _FakeSourceCandleRepo()
    client = cast(RedisClient, SimpleNamespace(client=_FakeWindowRedis()))
    cache = SourceWindowCache(client)
    service = SourceCandleService(cast(SourceCandleRepository, repo), cache)
    return service, repo, cache


def _closed() -> int:
    """
    Desc: Read when the window that has just closed opened at.
    Returns:
        return (int): The moment it opened, in whole seconds.
    """
    stamp = int(date_utils.utc_now().timestamp())
    return TimeFrame.FIVE_MINUTE.opened_at(stamp) - _five_minutes


def _candle(
    asset_id: int,
    prices: tuple[int, int, int, int],
    st_ts: int,
) -> CandleModel:
    """
    Desc: Build one five minute candle to roll up.
    Args:
        asset_id (int): ID of the asset it is of.
        prices (tuple[int, int, int, int]): Its open, high, low and close.
        st_ts (int): When it opened.
    Returns:
        return (CandleModel): The candle.
    """
    return CandleModel(
        asset_id=asset_id,
        timeframe=TimeFrame.FIVE_MINUTE,
        open=prices[0],
        high=prices[1],
        low=prices[2],
        close=prices[3],
        st_ts=st_ts,
        en_ts=st_ts + _five_minutes,
    )


class TestWritingTheClosedWindowDown:
    async def test_the_window_becomes_a_candle_of_its_own_span(self) -> None:
        service, repo, cache = _assets()
        closed = _closed()
        await cache.set(
            closed,
            AssetCode.GOLD18,
            AssetPriceWindow.opened(1, 100).folded(140).folded(110),
        )

        built = await service.build_from_cache()

        row = repo.rows[(1, TimeFrame.FIVE_MINUTE, closed)]
        assert built == 1
        assert (row.open, row.high, row.low, row.close) == (
            100,
            140,
            100,
            110,
        )
        assert (row.st_ts, row.en_ts) == (closed, closed + _five_minutes)

    async def test_the_window_is_dropped_once_it_is_written_down(
        self,
    ) -> None:
        service, _, cache = _assets()
        closed = _closed()
        await cache.set(
            closed, AssetCode.GOLD18, AssetPriceWindow.opened(1, 100)
        )

        await service.build_from_cache()

        assert await cache.get_all(closed) == {}

    async def test_a_window_nobody_priced_writes_nothing(self) -> None:
        service, repo, _ = _assets()

        built = await service.build_from_cache()

        assert built == 0
        assert repo.rows == {}

    async def test_every_source_of_a_line_becomes_a_candle(self) -> None:
        service, repo, cache = _sources()
        closed = _closed()
        await cache.set(
            closed,
            SymbolCode.GOLD18_GRAM,
            [
                SourcePriceWindow.opened(12, 1, 100).folded(140),
                SourcePriceWindow.opened(13, 1, 101),
            ],
        )

        built = await service.build_from_cache()

        assert built == 2
        assert {key[0]: row.close for key, row in repo.rows.items()} == {
            12: 140,
            13: 101,
        }


class TestRollingTheCoarserCandlesUp:
    async def test_the_hour_opens_on_the_first_and_closes_on_the_last(
        self,
    ) -> None:
        service, repo, _ = _assets()
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await repo.bulk_upsert(
            [
                _candle(1, (100, 120, 90, 110), hour),
                _candle(1, (110, 150, 105, 130), hour + _five_minutes),
                _candle(1, (130, 135, 80, 95), hour + 2 * _five_minutes),
            ]
        )

        built = await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        row = repo.rows[(1, TimeFrame.HOURLY, hour)]
        assert built == 1
        assert (row.open, row.high, row.low, row.close) == (100, 150, 80, 95)
        assert (row.st_ts, row.en_ts) == (
            hour,
            hour + TimeFrame.HOURLY.seconds,
        )

    async def test_each_asset_is_rolled_up_on_its_own(self) -> None:
        service, repo, _ = _assets()
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await repo.bulk_upsert(
            [
                _candle(1, (100, 120, 90, 110), hour),
                _candle(2, (1_900, 1_950, 1_890, 1_930), hour),
            ]
        )

        built = await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        assert built == 2
        assert repo.rows[(1, TimeFrame.HOURLY, hour)].close == 110
        assert repo.rows[(2, TimeFrame.HOURLY, hour)].close == 1_930

    async def test_a_candle_of_the_hour_before_is_left_out(self) -> None:
        service, repo, _ = _assets()
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await repo.bulk_upsert(
            [
                _candle(1, (50, 55, 45, 50), hour - _five_minutes),
                _candle(1, (100, 120, 90, 110), hour),
            ]
        )

        await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        row = repo.rows[(1, TimeFrame.HOURLY, hour)]
        assert (row.open, row.low) == (100, 90)

    async def test_the_finest_candle_is_rolled_from_nothing(self) -> None:
        service, repo, _ = _assets()
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await repo.bulk_upsert([_candle(1, (100, 120, 90, 110), hour)])

        built = await service.build_timeframe_from_rolled(
            TimeFrame.FIVE_MINUTE
        )

        assert built == 0

    async def test_a_window_with_no_finer_candle_writes_nothing(self) -> None:
        service, repo, _ = _assets()

        built = await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        assert built == 0
        assert repo.rows == {}
