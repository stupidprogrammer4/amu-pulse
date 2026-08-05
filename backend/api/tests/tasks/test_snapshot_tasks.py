from datetime import UTC, datetime

import pytest
from sqlmodel import select
from taskiq import InMemoryBroker

from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.tasks.snapshot import (
    snapshot_prices,
    snapshot_source_prices,
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
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.engine.domain.results import SourcePriceResult
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
from tests.tasks.conftest import TaskAssetPriceCache, TaskSourcePriceCache

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
_epoch = int(_at.timestamp())


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset with its default config.
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
        AssetCreate(title="دارایی", code=code, primary_color="#c8a44b")
    )
    return asset


async def _symbol(
    uow: PGUnitOfWork,
    asset: AssetModel,
    code: SymbolCode,
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
            title="خط",
            code=code,
            primary_color="#c8a44b",
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=CurrencyType.RIAL,
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
            primary_color="#c8a44b",
            source_type=SourceSwitch.IRAN_MARKET,
        )
    )
    return source


def _price(asset_id: int, price: int) -> AssetPriceResult:
    """
    Desc: Build one cached asset price.
    Args:
        asset_id (int): ID of the asset it belongs to.
        price (int): The mid price in rial.
    Returns:
        return (AssetPriceResult): The price.
    """
    return AssetPriceResult(
        asset_id=asset_id,
        buy_price=price,
        sell_price=price,
        price=price,
        buy_spread=0,
        sell_spread=0,
        buy_spread_rate=0.0,
        sell_spread_rate=0.0,
        priced_at=_at,
    )


def _reading(
    source_id: int,
    symbol_id: int,
    price: int,
) -> SourcePriceResult:
    """
    Desc: Build one cached source reading.
    Args:
        source_id (int): ID of the source that quoted it.
        symbol_id (int): ID of the line it was quoted for.
        price (int): The mid price in rial.
    Returns:
        return (SourcePriceResult): The reading.
    """
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=symbol_id,
        currency=CurrencyType.RIAL,
        buy_price=price,
        sell_price=price,
        price=price,
        buy_spread=0,
        sell_spread=0,
        buy_spread_rate=0.0,
        sell_spread_rate=0.0,
        priced_at=_at,
    )


class TestTheSchedule:
    def test_both_run_on_the_five_minute_marks(self) -> None:
        # :00, :05, :10 — the same grid for both, so points line up
        assert snapshot_prices.labels["schedule"] == [{"cron": "*/5 * * * *"}]
        assert snapshot_source_prices.labels["schedule"] == [
            {"cron": "*/5 * * * *"}
        ]

    def test_both_run_on_the_module_queue(self) -> None:
        assert snapshot_prices.labels["queue_name"] == "ticker_queue"
        assert snapshot_source_prices.labels["queue_name"] == "ticker_queue"


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSnapshotPrices:
    async def test_the_task_writes_a_point_per_priced_asset(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await TaskAssetPriceCache(caches).set_many(
            {
                AssetCode.GOLD18: _price(gold.id, 100_500_000),
                AssetCode.USD: _price(dollar.id, 1_905_000),
            }
        )
        await uow.commit()

        job = await snapshot_prices.kicker().with_broker(broker).kiq()  # type: ignore[call-arg]
        result = await job.wait_result()
        rows = (
            (await uow.session.execute(select(PriceTickerModel)))
            .scalars()
            .all()
        )

        assert result.is_err is False
        assert result.return_value is True
        assert {(row.asset_id, row.price) for row in rows} == {
            (gold.id, 100_500_000),
            (dollar.id, 1_905_000),
        }
        assert {row.timestamp for row in rows} == {_epoch}

    async def test_a_board_nobody_priced_writes_nothing(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        job = await snapshot_prices.kicker().with_broker(broker).kiq()  # type: ignore[call-arg]
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value is False


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSnapshotSourcePrices:
    async def test_the_task_writes_a_point_per_reading(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        gold = await _asset(uow)
        gram = await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        mazane = await _symbol(uow, gold, SymbolCode.GOLD18_MAZANE)
        source = await _source(uow)
        await TaskSourcePriceCache(caches).set_many(
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(source.id, gram.id, 100_500_000)
                ],
                SymbolCode.GOLD18_MAZANE: [
                    _reading(source.id, mazane.id, 4_331_802)
                ],
            }
        )
        await uow.commit()

        job = await snapshot_source_prices.kicker().with_broker(broker).kiq()  # type: ignore[call-arg]
        result = await job.wait_result()
        rows = (
            (await uow.session.execute(select(SourcePriceTickerModel)))
            .scalars()
            .all()
        )

        assert result.is_err is False
        assert result.return_value is True
        assert {(row.symbol_id, row.price) for row in rows} == {
            (gram.id, 100_500_000),
            (mazane.id, 4_331_802),
        }
        assert {row.source_id for row in rows} == {source.id}

    async def test_a_board_the_crawl_never_filled_writes_nothing(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        job = await snapshot_source_prices.kicker().with_broker(broker).kiq()  # type: ignore[call-arg]
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value is False
