from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from redis.exceptions import RedisError
from sqlmodel import col, select

from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient, resolve
from src.modules.chart.ticker.app.services import (
    PriceSnapshotService,
    SourcePriceSnapshotService,
)
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
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
from src.modules.price.calculator.app.services import (
    CacheReaderService as PriceCacheReaderService,
)
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)
from src.modules.price.engine.app.services import CacheReaderService
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.engine.infra.cache import (
    BubbleSourceCache,
    SourcePriceCache,
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

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
_epoch = int(_at.timestamp())


class TickerAssetPriceCache(AssetPriceCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:ticker:assets:price"


class TickerBubbleCache(BubbleCache):
    namespace = "test:ticker:bubble:price"


class TickerSourcePriceCache(SourcePriceCache):
    namespace = "test:ticker:sources:price"


class TickerBubbleSourceCache(BubbleSourceCache):
    namespace = "test:ticker:sources:bubble"


@pytest.fixture
async def caches(
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
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        await client.close()
        pytest.skip(f"redis is not reachable: {exc}")
    written = (
        TickerAssetPriceCache(client),
        TickerSourcePriceCache(client),
    )
    for cache in written:
        await cache.clear()
    try:
        yield client
    finally:
        for cache in written:
            await cache.clear()
        await client.close()


def _prices(uow: PGUnitOfWork, redis: RedisClient) -> PriceSnapshotService:
    """
    Desc: Build the asset snapshot service over the real table and cache.
    Args:
        uow (PGUnitOfWork): Unit of work the rows are written through.
        redis (RedisClient): Client the caches run on.
    Returns:
        return (PriceSnapshotService): The service.
    """
    reader = PriceCacheReaderService(
        TickerAssetPriceCache(redis), TickerBubbleCache(redis)
    )
    return PriceSnapshotService(PriceTickerRepository(uow), reader)


def _readings(
    uow: PGUnitOfWork,
    redis: RedisClient,
) -> SourcePriceSnapshotService:
    """
    Desc: Build the source snapshot service over the real table and cache.
    Args:
        uow (PGUnitOfWork): Unit of work the rows are written through.
        redis (RedisClient): Client the caches run on.
    Returns:
        return (SourcePriceSnapshotService): The service.
    """
    reader = CacheReaderService(
        TickerSourcePriceCache(redis), TickerBubbleSourceCache(redis)
    )
    return SourcePriceSnapshotService(SourcePriceTickerRepository(uow), reader)


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
        AssetCreate(title="طلا", code=code, primary_color="#c8a44b")
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


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestPriceSnapshot:
    async def test_the_board_lands_in_the_ticker_table(
        self, uow: PGUnitOfWork, caches: RedisClient
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await TickerAssetPriceCache(caches).set_many(
            {
                AssetCode.GOLD18: _price(gold.id, 100_500_000),
                AssetCode.USD: _price(dollar.id, 1_905_000),
            }
        )

        written = await _prices(uow, caches).snapshot_all()
        rows = (
            (
                await uow.session.execute(
                    select(PriceTickerModel).order_by(
                        col(PriceTickerModel.asset_id)
                    )
                )
            )
            .scalars()
            .all()
        )

        assert written is True
        assert [(row.asset_id, row.price) for row in rows] == [
            (gold.id, 100_500_000),
            (dollar.id, 1_905_000),
        ]
        assert {row.timestamp for row in rows} == {_epoch}

    async def test_two_sweeps_leave_two_points(
        self, uow: PGUnitOfWork, caches: RedisClient
    ) -> None:
        gold = await _asset(uow)
        await TickerAssetPriceCache(caches).set(
            AssetCode.GOLD18, _price(gold.id, 100_500_000)
        )
        service = _prices(uow, caches)

        await service.snapshot_all()
        await service.snapshot_all()
        rows = (
            (await uow.session.execute(select(PriceTickerModel)))
            .scalars()
            .all()
        )

        assert len(rows) == 2

    async def test_an_empty_board_writes_no_row(
        self, uow: PGUnitOfWork, caches: RedisClient
    ) -> None:
        written = await _prices(uow, caches).snapshot_all()
        rows = (
            (await uow.session.execute(select(PriceTickerModel)))
            .scalars()
            .all()
        )

        assert written is False
        assert list(rows) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourcePriceSnapshot:
    async def test_every_reading_lands_under_its_line(
        self, uow: PGUnitOfWork, caches: RedisClient
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        gram = await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        source = await _source(uow)
        await TickerSourcePriceCache(caches).set_many(
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(source.id, gram.id, 100_500_000)
                ],
                SymbolCode.USD_RIAL: [_reading(source.id, rial.id, 1_905_000)],
            }
        )

        written = await _readings(uow, caches).snapshot_all()
        rows = (
            (
                await uow.session.execute(
                    select(SourcePriceTickerModel).order_by(
                        col(SourcePriceTickerModel.symbol_id)
                    )
                )
            )
            .scalars()
            .all()
        )

        assert written is True
        assert [(row.symbol_id, row.price) for row in rows] == [
            (gram.id, 100_500_000),
            (rial.id, 1_905_000),
        ]
        assert {row.source_id for row in rows} == {source.id}
        assert {row.timestamp for row in rows} == {_epoch}

    async def test_two_sweeps_leave_two_points(
        self, uow: PGUnitOfWork, caches: RedisClient
    ) -> None:
        gold = await _asset(uow)
        gram = await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        source = await _source(uow)
        await TickerSourcePriceCache(caches).set(
            SymbolCode.GOLD18_GRAM,
            [_reading(source.id, gram.id, 100_500_000)],
        )
        service = _readings(uow, caches)

        await service.snapshot_all()
        await service.snapshot_all()
        rows = (
            (await uow.session.execute(select(SourcePriceTickerModel)))
            .scalars()
            .all()
        )

        assert len(rows) == 2

    async def test_an_empty_board_writes_no_row(
        self, uow: PGUnitOfWork, caches: RedisClient
    ) -> None:
        written = await _readings(uow, caches).snapshot_all()

        assert written is False
