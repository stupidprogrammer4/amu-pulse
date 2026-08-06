from datetime import UTC, datetime

import pytest
from taskiq import InMemoryBroker

from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
    AssetSwitchService,
)
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.dtos import (
    AssetCreate,
    AssetSwitchCreate,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.calculator.tasks.price import (
    calculate_asset,
    calculate_usd,
    reprice_asset,
)
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


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(
        AssetCreate(title="دارایی", code=code, primary_color="#c8a44b")
    )
    switches = AssetSwitchService(AssetSwitchRepository(uow))
    await switches.create(
        asset.id,
        AssetSwitchCreate(switch=SourceSwitch.IRAN_MARKET, priority=0),
    )
    return asset


async def _symbol(
    uow: PGUnitOfWork,
    asset: AssetModel,
    code: SymbolCode,
) -> SymbolModel:
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


def _reading(source_id: int, symbol_id: int, price: int):
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
class TestCalculateAsset:
    async def test_the_task_prices_the_asset_it_is_given(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        gold = await _asset(uow)
        gram = await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        source = await _source(uow)
        await TaskSourcePriceCache(caches).set(
            SymbolCode.GOLD18_GRAM,
            [_reading(source.id, gram.id, 100_500_000)],
        )
        await uow.commit()

        job = await (
            calculate_asset.kicker().with_broker(broker).kiq(asset_id=gold.id)  # type: ignore[call-arg]
        )
        result = await job.wait_result()
        priced = await TaskAssetPriceCache(caches).get(AssetCode.GOLD18)

        assert result.is_err is False
        assert result.return_value == 100_500_000
        assert priced is not None
        assert priced.price == 100_500_000

    async def test_an_asset_nobody_quoted_prices_at_zero(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        gold = await _asset(uow)
        await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        await uow.commit()

        job = await (
            calculate_asset.kicker().with_broker(broker).kiq(asset_id=gold.id)  # type: ignore[call-arg]
        )
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value == 0

    async def test_an_asset_that_does_not_exist_errors(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        job = await (
            calculate_asset.kicker().with_broker(broker).kiq(asset_id=9999)  # type: ignore[call-arg]
        )
        result = await job.wait_result()

        assert result.is_err is True


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestRepriceAsset:
    async def test_the_task_prices_the_code_it_is_given(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        dollar = await _asset(uow, AssetCode.USD)
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        source = await _source(uow)
        await TaskSourcePriceCache(caches).set(
            SymbolCode.USD_RIAL, [_reading(source.id, rial.id, 1_905_000)]
        )
        await uow.commit()

        job = await (
            reprice_asset.kicker().with_broker(broker).kiq(code=AssetCode.USD)  # type: ignore[call-arg]
        )
        result = await job.wait_result()
        priced = await TaskAssetPriceCache(caches).get(AssetCode.USD)

        assert result.is_err is False
        assert result.return_value == 1_905_000
        assert priced is not None

    async def test_a_code_no_asset_carries_prices_at_zero(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        job = await (
            reprice_asset.kicker()
            .with_broker(broker)
            .kiq(code=AssetCode.GOLD18)  # type: ignore[call-arg]
        )
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value == 0


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestCalculateUsd:
    async def test_the_task_prices_the_dollar(
        self,
        uow: PGUnitOfWork,
        caches: RedisClient,
        broker: InMemoryBroker,
    ) -> None:
        dollar = await _asset(uow, AssetCode.USD)
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        source = await _source(uow)
        await TaskSourcePriceCache(caches).set(
            SymbolCode.USD_RIAL, [_reading(source.id, rial.id, 1_905_000)]
        )
        await uow.commit()

        job = await calculate_usd.kicker().with_broker(broker).kiq()  # type: ignore[call-arg]
        result = await job.wait_result()

        assert result.is_err is False
        assert result.return_value == 1_905_000

    async def test_it_runs_every_twenty_seconds(self) -> None:
        assert calculate_usd.labels["schedule"] == [{"interval": 20}]
