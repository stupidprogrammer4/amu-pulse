from collections.abc import AsyncIterator

import pytest
from taskiq import InMemoryBroker

from src.common.utils import date_utils
from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.domain.windows import (
    AssetPriceWindow,
    SourcePriceWindow,
)
from src.modules.chart.candle.infra.repository import (
    CandleRepository,
    SourceCandleRepository,
)
from src.modules.chart.candle.tasks.build import (
    build_from_cache,
    roll_timeframe,
)
from src.modules.price.assets.app.services import (
    AssetConfigService,
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
from src.modules.price.symbols.domain.dtos import SymbolCreate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.domain.models import SymbolModel
from src.modules.price.symbols.infra.repository import SymbolRepository
from tests.conftest import NullScheduler
from tests.tasks.conftest import (
    TaskAssetWindowCache,
    TaskSourceWindowCache,
)

_five_minutes = TimeFrame.FIVE_MINUTE.seconds


def _closed() -> int:
    """
    Desc: Read when the window that has just closed opened at.
    Returns:
        return (int): The moment it opened, in whole seconds.
    """
    stamp = int(date_utils.utc_now().timestamp())
    return TimeFrame.FIVE_MINUTE.opened_at(stamp) - _five_minutes


@pytest.fixture
async def windows(caches: RedisClient) -> AsyncIterator[RedisClient]:
    written = (
        TaskAssetWindowCache(caches),
        TaskSourceWindowCache(caches),
    )
    for cache in written:
        await cache.remove(_closed())
    try:
        yield caches
    finally:
        for cache in written:
            await cache.remove(_closed())


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
) -> SymbolModel:
    """
    Desc: Create the line an asset is quoted through.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the line belongs to.
    Returns:
        return (SymbolModel): The created line.
    """
    symbols = SymbolService(SymbolRepository(uow))
    symbol = await symbols.create(
        SymbolCreate(
            title="هر گرم",
            code=SymbolCode.GOLD18_GRAM,
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=CurrencyType.RIAL,
            primary_color="#c8a44b",
        )
    )
    return symbol


async def _source(uow: PGUnitOfWork) -> SourceModel:
    """
    Desc: Create one source feeding the Iranian market.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (SourceModel): The created source.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    sources = SourceService(SourceRepository(uow), configs)
    source = await sources.create(
        SourceCreate(
            title="منبع",
            code=SourceCode.TGJU,
            website_url="https://example.test",
            icon_url="/storage/file/ab/x.png",
            primary_color="#4b8ec8",
            source_type=SourceSwitch.IRAN_MARKET,
        )
    )
    return source


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBuildFromCache:
    async def test_the_task_writes_the_closed_window_down(
        self,
        uow: PGUnitOfWork,
        windows: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        await uow.commit()
        closed = _closed()
        await TaskAssetWindowCache(windows).set(
            closed,
            AssetCode.GOLD18,
            AssetPriceWindow.opened(asset.id, 100).folded(140),
        )
        await TaskSourceWindowCache(windows).set(
            closed,
            SymbolCode.GOLD18_GRAM,
            [SourcePriceWindow.opened(source.id, symbol.id, 101)],
        )

        job = await build_from_cache.kicker().with_broker(broker).kiq()
        result = await job.wait_result()

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, closed, closed + _five_minutes
        )
        quoted = await SourceCandleRepository(uow).get_by_timeframe(
            source.id,
            symbol.id,
            TimeFrame.FIVE_MINUTE,
            closed,
            closed + _five_minutes,
        )
        assert result.is_err is False
        assert result.return_value == 2
        assert (found[0].open, found[0].high) == (100, 140)
        assert quoted[0].close == 101

    async def test_a_window_nobody_priced_writes_nothing(
        self,
        uow: PGUnitOfWork,
        windows: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        job = await build_from_cache.kicker().with_broker(broker).kiq()
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value == 0


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestRollTimeframe:
    async def test_the_task_rolls_the_timeframe_it_is_given_up(
        self,
        uow: PGUnitOfWork,
        windows: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        asset = await _asset(uow)
        await uow.commit()
        closed = _closed()
        hour = TimeFrame.HOURLY.opened_at(closed)
        await TaskAssetWindowCache(windows).set(
            closed,
            AssetCode.GOLD18,
            AssetPriceWindow.opened(asset.id, 100).folded(140).folded(90),
        )
        await build_from_cache.kicker().with_broker(broker).kiq()

        job = await (
            roll_timeframe.kicker()
            .with_broker(broker)
            .kiq(tf=TimeFrame.HOURLY)  # type: ignore[call-arg]
        )
        result = await job.wait_result()

        found = await CandleRepository(uow).get_by_timeframe(
            asset.id, TimeFrame.HOURLY, hour, hour + TimeFrame.HOURLY.seconds
        )
        assert result.is_err is False
        assert result.return_value == 1
        assert (found[0].open, found[0].high, found[0].close) == (
            100,
            140,
            90,
        )

    async def test_the_finest_timeframe_rolls_up_nothing(
        self,
        uow: PGUnitOfWork,
        windows: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        job = await (
            roll_timeframe.kicker()
            .with_broker(broker)
            .kiq(tf=TimeFrame.FIVE_MINUTE)  # type: ignore[call-arg]
        )
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value == 0


class TestWhatTheSchedulesSay:
    async def test_the_window_is_written_down_on_the_five_minute_marks(
        self,
    ) -> None:
        schedules = build_from_cache.labels["schedule"]

        assert [row["cron"] for row in schedules] == ["*/5 * * * *"]

    async def test_each_timeframe_is_rolled_up_on_tehrans_clock(
        self,
    ) -> None:
        schedules = roll_timeframe.labels["schedule"]

        assert [(row["cron"], row["kwargs"]["tf"]) for row in schedules] == [
            ("1 * * * *", TimeFrame.HOURLY.value),
            ("2 */5 * * *", TimeFrame.FIVE_HOURLY.value),
            ("3 0 * * *", TimeFrame.DAILY.value),
        ]
        assert {row["cron_offset"] for row in schedules} == {"Asia/Tehran"}
