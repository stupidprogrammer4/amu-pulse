from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from redis.exceptions import RedisError

from src.common.errors.exceptions import ValidationException
from src.common.utils import date_utils
from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient, resolve
from src.modules.chart.candle.app.services import (
    CandleService,
    SourceCandleService,
)
from src.modules.chart.candle.domain.dtos import ParamDTO, SourceParamDTO
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.domain.models import CandleModel
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
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetMetaService,
    AssetService,
)
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceMetaService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.config.constants import SYMBOL_ID_ENCRYPTION
from src.modules.price.symbols.domain.dtos import SymbolCreate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.domain.models import SymbolModel
from src.modules.price.symbols.infra.repository import SymbolRepository
from tests.conftest import NullScheduler

_five_minutes = TimeFrame.FIVE_MINUTE.seconds


class _TestAssetWindowCache(AssetWindowCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:build:assets:window"


class _TestSourceWindowCache(SourceWindowCache):
    namespace = "test:build:sources:window"


def _closed() -> int:
    """
    Desc: Read when the window that has just closed opened at.
    Returns:
        return (int): The moment it opened, in whole seconds.
    """
    stamp = int(date_utils.utc_now().timestamp())
    return TimeFrame.FIVE_MINUTE.opened_at(stamp) - _five_minutes


@pytest.fixture
async def redis(
    integration_settings: Settings,
) -> AsyncIterator[RedisClient]:
    client = RedisClient(
        integration_settings.redis.url,
        max_connections=2,
        socket_timeout=integration_settings.redis.socket_timeout,
        socket_connect_timeout=(
            integration_settings.redis.socket_connect_timeout
        ),
        health_check_interval=(
            integration_settings.redis.health_check_interval
        ),
    )
    try:
        # reaching redis at all is what decides whether these can run
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        await client.close()
        pytest.skip(f"redis is not reachable: {exc}")
    caches = (
        _TestAssetWindowCache(client),
        _TestSourceWindowCache(client),
    )
    for cache in caches:
        await cache.remove(_closed())
    try:
        yield client
    finally:
        for cache in caches:
            await cache.remove(_closed())
        await client.close()


def _asset_meta(uow: PGUnitOfWork) -> AssetMetaService:
    """
    Desc: Build the asset meta service over the real services.
    Args:
        uow (PGUnitOfWork): Unit of work to read through.
    Returns:
        return (AssetMetaService): What names a charted asset.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    return AssetMetaService(AssetService(AssetRepository(uow), configs))


def _source_meta(uow: PGUnitOfWork) -> SourceMetaService:
    """
    Desc: Build the source meta service over the real services.
    Args:
        uow (PGUnitOfWork): Unit of work to read through.
    Returns:
        return (SourceMetaService): What names a charted source and line.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    return SourceMetaService(
        SourceService(SourceRepository(uow), configs),
        SymbolService(SymbolRepository(uow)),
    )


def _candles(
    uow: PGUnitOfWork,
    cache: AssetWindowCache,
) -> CandleService:
    """
    Desc: Build the candle service over the real table and cache.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        cache (AssetWindowCache): Where the open window lives.
    Returns:
        return (CandleService): The service.
    """
    return CandleService(CandleRepository(uow), cache, _asset_meta(uow))


def _source_candles(
    uow: PGUnitOfWork,
    cache: SourceWindowCache,
) -> SourceCandleService:
    """
    Desc: Build the source candle service over the real table and cache.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        cache (SourceWindowCache): Where the open window lives.
    Returns:
        return (SourceCandleService): The service.
    """
    return SourceCandleService(
        SourceCandleRepository(uow), cache, _source_meta(uow)
    )


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset to hang candles off.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(
        AssetCreate(title="طلا", code=code, primary_color="#c8a44b")
    )
    return asset


async def _symbol(
    uow: PGUnitOfWork,
    asset: AssetModel,
    code: SymbolCode = SymbolCode.GOLD18_GRAM,
) -> SymbolModel:
    """
    Desc: Create the line an asset is quoted through.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the line belongs to.
        code (SymbolCode): Code of the line.
    Returns:
        return (SymbolModel): The created line.
    """
    symbols = SymbolService(SymbolRepository(uow))
    symbol = await symbols.create(
        SymbolCreate(
            title="هر گرم",
            code=code,
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=CurrencyType.RIAL,
            primary_color="#c8a44b",
        )
    )
    return symbol


async def _source(
    uow: PGUnitOfWork,
    code: SourceCode = SourceCode.TGJU,
) -> SourceModel:
    """
    Desc: Create one source feeding the Iranian market.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (SourceCode): Code of the source.
    Returns:
        return (SourceModel): The created source.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    sources = SourceService(SourceRepository(uow), configs)
    source = await sources.create(
        SourceCreate(
            title="منبع",
            code=code,
            website_url="https://example.test",
            icon_url="/storage/file/ab/x.png",
            primary_color="#4b8ec8",
            source_type=SourceSwitch.IRAN_MARKET,
        )
    )
    return source


async def _five_minute_candles(
    uow: PGUnitOfWork,
    asset: AssetModel,
    prices: list[tuple[int, int, int, int]],
    st_ts: int,
) -> None:
    """
    Desc: Write one five minute candle per step, oldest first.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the candles are of.
        prices (list[tuple[int, int, int, int]]): The open, high, low and
            close of each candle.
        st_ts (int): When the first candle opened.
    """
    repo = CandleRepository(uow)
    await repo.bulk_upsert(
        [
            CandleModel(
                asset_id=asset.id,
                timeframe=TimeFrame.FIVE_MINUTE,
                open=row[0],
                high=row[1],
                low=row[2],
                close=row[3],
                st_ts=st_ts + step * _five_minutes,
                en_ts=st_ts + (step + 1) * _five_minutes,
            )
            for step, row in enumerate(prices)
        ]
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestWritingTheClosedWindowDown:
    async def test_every_asset_of_the_window_becomes_a_candle(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(uow)
        usd = await _asset(uow, AssetCode.USD)
        cache = _TestAssetWindowCache(redis)
        closed = _closed()
        await cache.set_many(
            closed,
            {
                AssetCode.GOLD18: AssetPriceWindow.opened(gold.id, 100)
                .folded(140)
                .folded(110),
                AssetCode.USD: AssetPriceWindow.opened(usd.id, 1_900),
            },
        )
        service = _candles(uow, cache)

        built = await service.build_from_cache()

        found = await CandleRepository(uow).get_by_timeframe(
            gold.id, TimeFrame.FIVE_MINUTE, closed, closed + _five_minutes
        )
        assert built == 2
        assert len(found) == 1
        assert (
            found[0].open,
            found[0].high,
            found[0].low,
            found[0].close,
        ) == (100, 140, 100, 110)
        assert (found[0].st_ts, found[0].en_ts) == (
            closed,
            closed + _five_minutes,
        )

    async def test_the_window_is_dropped_once_it_is_written_down(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        cache = _TestAssetWindowCache(redis)
        closed = _closed()
        await cache.set(
            closed, AssetCode.GOLD18, AssetPriceWindow.opened(asset.id, 100)
        )
        service = _candles(uow, cache)

        await service.build_from_cache()

        assert await cache.get_all(closed) == {}

    async def test_a_rerun_writes_the_same_candle_again(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        cache = _TestAssetWindowCache(redis)
        closed = _closed()
        await cache.set(
            closed, AssetCode.GOLD18, AssetPriceWindow.opened(asset.id, 100)
        )
        service = _candles(uow, cache)

        await service.build_from_cache()
        built = await service.build_from_cache()

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, closed, closed + _five_minutes
        )
        assert built == 0
        assert len(found) == 1

    async def test_a_window_nobody_priced_writes_nothing(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        service = _candles(uow, _TestAssetWindowCache(redis))

        built = await service.build_from_cache()

        assert built == 0

    async def test_every_source_of_the_window_becomes_a_candle(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        tgju = await _source(uow)
        alanchand = await _source(uow, SourceCode.ALANCHAND)
        cache = _TestSourceWindowCache(redis)
        closed = _closed()
        await cache.set(
            closed,
            SymbolCode.GOLD18_GRAM,
            [
                SourcePriceWindow.opened(tgju.id, symbol.id, 100).folded(140),
                SourcePriceWindow.opened(alanchand.id, symbol.id, 101),
            ],
        )
        service = _source_candles(uow, cache)

        built = await service.build_from_cache()

        found = await SourceCandleRepository(uow).get_by_timeframe(
            tgju.id,
            symbol.id,
            TimeFrame.FIVE_MINUTE,
            closed,
            closed + _five_minutes,
        )
        assert built == 2
        assert (found[0].open, found[0].high, found[0].close) == (
            100,
            140,
            140,
        )
        assert await cache.get_all(closed) == {}


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestRollingTheCoarserCandlesUp:
    async def test_the_hour_opens_on_the_first_and_closes_on_the_last(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        closed = _closed()
        hour = TimeFrame.HOURLY.opened_at(closed)
        await _five_minute_candles(
            uow,
            asset,
            [(100, 120, 90, 110), (110, 150, 105, 130), (130, 135, 80, 95)],
            hour,
        )
        service = _candles(uow, _TestAssetWindowCache(redis))

        built = await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.HOURLY, hour, hour + TimeFrame.HOURLY.seconds
        )
        assert built == 1
        assert (
            found[0].open,
            found[0].high,
            found[0].low,
            found[0].close,
        ) == (100, 150, 80, 95)
        assert (found[0].st_ts, found[0].en_ts) == (
            hour,
            hour + TimeFrame.HOURLY.seconds,
        )

    async def test_each_asset_is_rolled_up_on_its_own(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(uow)
        usd = await _asset(uow, AssetCode.USD)
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await _five_minute_candles(
            uow, gold, [(100, 120, 90, 110), (110, 130, 100, 120)], hour
        )
        await _five_minute_candles(
            uow, usd, [(1_900, 1_950, 1_890, 1_930)], hour
        )
        service = _candles(uow, _TestAssetWindowCache(redis))

        built = await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        rolled = await CandleRepository(uow).get_all_by_timeframe(
            TimeFrame.HOURLY, hour, hour + TimeFrame.HOURLY.seconds
        )
        assert built == 2
        assert {row.asset_id: row.close for row in rolled} == {
            gold.id: 120,
            usd.id: 1_930,
        }

    async def test_a_candle_of_the_hour_before_is_left_out(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await _five_minute_candles(
            uow, asset, [(50, 55, 45, 50)], hour - TimeFrame.HOURLY.seconds
        )
        await _five_minute_candles(uow, asset, [(100, 120, 90, 110)], hour)
        service = _candles(uow, _TestAssetWindowCache(redis))

        await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.HOURLY, hour, hour + TimeFrame.HOURLY.seconds
        )
        assert (found[0].open, found[0].low) == (100, 90)

    async def test_the_day_is_rolled_up_out_of_the_hours(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        closed = _closed()
        hour = TimeFrame.HOURLY.opened_at(closed)
        day = TimeFrame.DAILY.opened_at(closed)
        await _five_minute_candles(uow, asset, [(100, 150, 80, 95)], hour)
        service = _candles(uow, _TestAssetWindowCache(redis))

        await service.build_timeframe_from_rolled(TimeFrame.HOURLY)
        built = await service.build_timeframe_from_rolled(TimeFrame.DAILY)

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.DAILY, day, day + TimeFrame.DAILY.seconds
        )
        assert built == 1
        assert (found[0].open, found[0].high, found[0].close) == (100, 150, 95)

    async def test_a_rerun_rewrites_the_rolled_candle(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await _five_minute_candles(uow, asset, [(100, 120, 90, 110)], hour)
        service = _candles(uow, _TestAssetWindowCache(redis))

        await service.build_timeframe_from_rolled(TimeFrame.HOURLY)
        await _five_minute_candles(
            uow, asset, [(100, 120, 90, 110), (110, 160, 70, 80)], hour
        )
        await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.HOURLY, hour, hour + TimeFrame.HOURLY.seconds
        )
        assert len(found) == 1
        assert (found[0].high, found[0].low, found[0].close) == (160, 70, 80)

    async def test_the_finest_candle_is_rolled_from_nothing(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        hour = TimeFrame.HOURLY.opened_at(_closed())
        await _five_minute_candles(uow, asset, [(100, 120, 90, 110)], hour)
        service = _candles(uow, _TestAssetWindowCache(redis))

        built = await service.build_timeframe_from_rolled(
            TimeFrame.FIVE_MINUTE
        )

        assert built == 0

    async def test_every_source_and_line_is_rolled_up_on_its_own(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        tgju = await _source(uow)
        alanchand = await _source(uow, SourceCode.ALANCHAND)
        cache = _TestSourceWindowCache(redis)
        closed = _closed()
        hour = TimeFrame.HOURLY.opened_at(closed)
        await cache.set(
            closed,
            SymbolCode.GOLD18_GRAM,
            [
                SourcePriceWindow.opened(tgju.id, symbol.id, 100).folded(140),
                SourcePriceWindow.opened(alanchand.id, symbol.id, 101),
            ],
        )
        service = _source_candles(uow, cache)
        await service.build_from_cache()

        built = await service.build_timeframe_from_rolled(TimeFrame.HOURLY)

        rolled = await SourceCandleRepository(uow).get_all_by_timeframe(
            TimeFrame.HOURLY, hour, hour + TimeFrame.HOURLY.seconds
        )
        assert built == 2
        assert {row.source_id: row.high for row in rolled} == {
            tgju.id: 140,
            alanchand.id: 101,
        }


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestDrawingTheCandlesAsked:
    async def test_the_chart_is_drawn_on_the_timeframe_of_its_span(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        closed = _closed()
        await _five_minute_candles(
            uow, asset, [(100, 120, 90, 110), (110, 150, 105, 130)], closed
        )
        service = _candles(uow, _TestAssetWindowCache(redis))
        ends = datetime.fromtimestamp(closed + 2 * _five_minutes, UTC)
        param = ParamDTO(
            from_datetime=datetime.fromtimestamp(closed, UTC),
            to_datetime=ends,
        )

        result = await service.get_candle(asset.id, param)

        assert result.data.timeframe is TimeFrame.FIVE_MINUTE
        assert [row.close for row in result.data.candles] == [110, 130]
        assert result.data.from_timestamp == closed

    async def test_the_charted_asset_is_named_in_the_meta(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        closed = _closed()
        await _five_minute_candles(uow, asset, [(100, 120, 90, 110)], closed)
        service = _candles(uow, _TestAssetWindowCache(redis))
        param = ParamDTO(
            from_datetime=datetime.fromtimestamp(closed, UTC),
            to_datetime=datetime.fromtimestamp(closed + _five_minutes, UTC),
        )

        result = await service.get_candle(asset.id, param)

        assert [row.code for row in result.meta.assets] == [AssetCode.GOLD18]

    async def test_a_longer_span_is_drawn_on_a_coarser_candle(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        service = _candles(uow, _TestAssetWindowCache(redis))
        ends = date_utils.utc_now()
        param = ParamDTO(
            from_datetime=ends - timedelta(days=30), to_datetime=ends
        )

        result = await service.get_candle(asset.id, param)

        assert result.data.timeframe is TimeFrame.FIVE_HOURLY
        assert result.data.candles == []

    async def test_a_span_of_a_year_or_more_is_turned_away(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        service = _candles(uow, _TestAssetWindowCache(redis))
        ends = date_utils.utc_now()
        param = ParamDTO(
            from_datetime=ends - timedelta(days=400), to_datetime=ends
        )

        with pytest.raises(ValidationException):
            await service.get_candle(asset.id, param)

    async def test_what_one_source_quoted_is_drawn_and_named(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        cache = _TestSourceWindowCache(redis)
        closed = _closed()
        await cache.set(
            closed,
            SymbolCode.GOLD18_GRAM,
            [SourcePriceWindow.opened(source.id, symbol.id, 100).folded(140)],
        )
        service = _source_candles(uow, cache)
        await service.build_from_cache()
        param = SourceParamDTO(
            symbol_id=SYMBOL_ID_ENCRYPTION.encode(symbol.id),
            from_datetime=datetime.fromtimestamp(closed, UTC),
            to_datetime=datetime.fromtimestamp(closed + _five_minutes, UTC),
        )

        result = await service.get_candle(source.id, param)

        assert result.data.timeframe is TimeFrame.FIVE_MINUTE
        assert [row.high for row in result.data.candles] == [140]
        assert [row.code for row in result.meta.sources] == [SourceCode.TGJU]
        assert [row.code for row in result.meta.symbols] == [
            SymbolCode.GOLD18_GRAM
        ]
