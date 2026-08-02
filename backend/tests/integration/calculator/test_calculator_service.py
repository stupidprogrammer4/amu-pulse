from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from redis.exceptions import RedisError

from src.common.errors.exceptions import NotFoundException
from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient, resolve
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
from src.modules.price.calculator.app.services import CalculatorService
from src.modules.price.calculator.domain.results import BubbleResult
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)
from src.modules.price.calculator.infra.readers import (
    AssetReader,
    SourceReader,
    SwitchOrderReader,
    SymbolReader,
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

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


class _TestAssetPriceCache(AssetPriceCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:calc:assets:price"


class _TestBubbleCache(BubbleCache):
    namespace = "test:calc:settled:bubble"


class _TestSourcePriceCache(SourcePriceCache):
    namespace = "test:calc:crawl:price"


class _TestBubbleSourceCache(BubbleSourceCache):
    namespace = "test:calc:crawl:bubble"


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
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        await client.close()
        pytest.skip(f"redis is not reachable: {exc}")
    caches = (
        _TestAssetPriceCache(client),
        _TestBubbleCache(client),
        _TestSourcePriceCache(client),
    )
    for cache in caches:
        await cache.clear()
    try:
        yield client
    finally:
        for cache in caches:
            await cache.clear()
        await client.close()


def _service(
    uow: PGUnitOfWork,
    redis: RedisClient,
) -> tuple[CalculatorService, _TestAssetPriceCache]:
    """
    Desc: Build the service over the real database, redis and engine reader.
    Args:
        uow (PGUnitOfWork): Unit of work the tables are read through.
        redis (RedisClient): Client every cache runs on.
    Returns:
        return (tuple[CalculatorService, _TestAssetPriceCache]): The service
            and the cache it prices into.
    """
    prices = _TestAssetPriceCache(redis)
    readings = CacheReaderService(
        _TestSourcePriceCache(redis),
        _TestBubbleSourceCache(redis),
    )
    service = CalculatorService(
        AssetReader(uow),
        SymbolReader(uow),
        SwitchOrderReader(uow),
        SourceReader(uow),
        readings,
        _TestBubbleCache(redis),
        prices,
    )
    return service, prices


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode,
    switches: list[SourceSwitch],
) -> AssetModel:
    """
    Desc: Create one asset with its config and its pricing order.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
        switches (list[SourceSwitch]): Its markets, first tried first.
    Returns:
        return (AssetModel): The created asset.
    """
    configs = AssetConfigService(AssetConfigRepository(uow))
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(AssetCreate(title="دارایی", code=code))
    order = AssetSwitchService(AssetSwitchRepository(uow))
    for priority, switch in enumerate(switches):
        await order.create(
            asset.id,
            AssetSwitchCreate(switch=switch, priority=priority),
        )
    return asset


async def _symbol(
    uow: PGUnitOfWork,
    asset: AssetModel,
    code: SymbolCode,
    currency: CurrencyType = CurrencyType.RIAL,
) -> SymbolModel:
    """
    Desc: Create one line the asset is quoted through.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the line belongs to.
        code (SymbolCode): Code of the line.
        currency (CurrencyType): What the line is priced in.
    Returns:
        return (SymbolModel): The created line.
    """
    symbols = SymbolService(SymbolRepository(uow))
    symbol = await symbols.create(
        SymbolCreate(
            title="خط",
            code=code,
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=currency,
        )
    )
    return symbol


async def _source(
    uow: PGUnitOfWork,
    code: SourceCode,
    switch: SourceSwitch,
) -> SourceModel:
    """
    Desc: Create one source feeding the given market.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (SourceCode): Code of the source.
        switch (SourceSwitch): The market it feeds.
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
            primary_color="#c8a44b",
            source_type=switch,
        )
    )
    return source


def _reading(
    buying: int,
    selling: int,
    source_id: int,
    symbol_id: int,
    currency: CurrencyType = CurrencyType.RIAL,
) -> SourcePriceResult:
    """
    Desc: Build one source reading, mid priced like the crawl caches it.
    Args:
        buying (int): The buying side, in the currency's own unit.
        selling (int): The selling side, in the currency's own unit.
        source_id (int): ID of the source that quoted it.
        symbol_id (int): ID of the line it was quoted for.
        currency (CurrencyType): What the two sides are counted in.
    Returns:
        return (SourcePriceResult): The reading.
    """
    price = round((buying + selling) / 2)
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=symbol_id,
        currency=currency,
        buy_price=buying,
        sell_price=selling,
        price=price,
        buy_spread=price - buying,
        sell_spread=selling - price,
        buy_spread_rate=(price - buying) / price,
        sell_spread_rate=(selling - price) / price,
        priced_at=_at,
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestCalculateOne:
    async def test_it_prices_gold_off_the_iranian_market(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(
            uow,
            AssetCode.GOLD18,
            [SourceSwitch.IRAN_MARKET, SourceSwitch.SUPPLIER],
        )
        gram = await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        await _symbol(uow, gold, SymbolCode.GOLD18_MAZANE)
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set(
            SymbolCode.GOLD18_GRAM,
            [_reading(100_000_000, 101_000_000, iran.id, gram.id)],
        )
        service, cache = _service(uow, redis)

        price = await service.calculate(gold.id)
        found = await cache.get(AssetCode.GOLD18)

        assert price == 100_500_000
        assert found is not None
        assert found.asset_id == gold.id

    async def test_it_falls_through_to_the_suppliers(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        # the iranian sources went quiet, so the mazane prices gold
        gold = await _asset(
            uow,
            AssetCode.GOLD18,
            [SourceSwitch.IRAN_MARKET, SourceSwitch.SUPPLIER],
        )
        await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        mazane = await _symbol(uow, gold, SymbolCode.GOLD18_MAZANE)
        await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        supplier = await _source(
            uow, SourceCode.TALALAND, SourceSwitch.SUPPLIER
        )
        await _TestSourcePriceCache(redis).set(
            SymbolCode.GOLD18_MAZANE,
            [_reading(4_331_802, 4_331_802, supplier.id, mazane.id)],
        )
        service, _ = _service(uow, redis)

        price = await service.calculate(gold.id)

        assert price == 1_000_000

    async def test_a_market_off_the_order_never_prices(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(uow, AssetCode.GOLD18, [SourceSwitch.SUPPLIER])
        gram = await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set(
            SymbolCode.GOLD18_GRAM,
            [_reading(100_000_000, 101_000_000, iran.id, gram.id)],
        )
        service, cache = _service(uow, redis)

        price = await service.calculate(gold.id)

        assert price == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_the_world_prices_gold_off_the_dollar_and_the_premium(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(
            uow, AssetCode.GOLD18, [SourceSwitch.GLOBAL_MARKET]
        )
        dollar = await _asset(uow, AssetCode.USD, [SourceSwitch.IRAN_MARKET])
        ounce = await _symbol(
            uow, gold, SymbolCode.XAU_OUNCE, CurrencyType.USD
        )
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        world = await _source(
            uow, SourceCode.GOLD_API, SourceSwitch.GLOBAL_MARKET
        )
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set_many(
            {
                SymbolCode.XAU_OUNCE: [
                    _reading(
                        400_000,
                        400_000,
                        world.id,
                        ounce.id,
                        CurrencyType.USD,
                    )
                ],
                SymbolCode.USD_RIAL: [
                    _reading(1_000_000, 1_000_000, iran.id, rial.id)
                ],
            }
        )
        await _TestBubbleCache(redis).set(
            AssetCode.GOLD18,
            BubbleResult(asset_id=gold.id, amount=5_000_000, priced_at=_at),
        )
        service, cache = _service(uow, redis)

        # the dollar has to be priced first; the world reads it from cache
        await service.calculate_usd()
        price = await service.calculate(gold.id)
        found = await cache.get(AssetCode.GOLD18)

        assert price == 101_452_240
        assert found is not None

    async def test_an_asset_that_does_not_exist(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        service, _ = _service(uow, redis)

        with pytest.raises(NotFoundException):
            await service.calculate(9999)


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestCalculateUsd:
    async def test_it_prices_the_dollar_without_being_told_its_id(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        dollar = await _asset(uow, AssetCode.USD, [SourceSwitch.IRAN_MARKET])
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set(
            SymbolCode.USD_RIAL,
            [_reading(1_900_000, 1_910_000, iran.id, rial.id)],
        )
        service, cache = _service(uow, redis)

        price = await service.calculate_usd()
        found = await cache.get(AssetCode.USD)

        assert price == 1_905_000
        assert found is not None
        assert found.asset_id == dollar.id

    async def test_no_dollar_asset_at_all(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        await _asset(uow, AssetCode.GOLD18, [SourceSwitch.IRAN_MARKET])
        service, _ = _service(uow, redis)

        with pytest.raises(NotFoundException):
            await service.calculate_usd()


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestCalculateAll:
    async def test_the_sweep_leaves_the_dollar_to_its_own_route(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(
            uow,
            AssetCode.GOLD18,
            [SourceSwitch.SUPPLIER, SourceSwitch.IRAN_MARKET],
        )
        dollar = await _asset(uow, AssetCode.USD, [SourceSwitch.IRAN_MARKET])
        mazane = await _symbol(uow, gold, SymbolCode.GOLD18_MAZANE)
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        supplier = await _source(
            uow, SourceCode.TALALAND, SourceSwitch.SUPPLIER
        )
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set_many(
            {
                SymbolCode.GOLD18_MAZANE: [
                    _reading(4_331_802, 4_331_802, supplier.id, mazane.id)
                ],
                SymbolCode.USD_RIAL: [
                    _reading(1_900_000, 1_910_000, iran.id, rial.id)
                ],
            }
        )
        service, cache = _service(uow, redis)

        priced = await service.calculate_all()
        found = await cache.get_all()

        assert priced == 1
        assert {code: r.price for code, r in found.items()} == {
            AssetCode.GOLD18: 1_000_000
        }

    async def test_the_sweep_skips_what_the_crawl_never_reached(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(uow, AssetCode.GOLD18, [SourceSwitch.IRAN_MARKET])
        dollar = await _asset(uow, AssetCode.USD, [SourceSwitch.IRAN_MARKET])
        await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set(
            SymbolCode.USD_RIAL,
            [_reading(1_900_000, 1_910_000, iran.id, rial.id)],
        )
        service, cache = _service(uow, redis)

        priced = await service.calculate_all()

        assert priced == 0
        assert await cache.get_all() == {}

    async def test_the_sweep_prices_gold_off_the_dollar_route_left(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        gold = await _asset(
            uow, AssetCode.GOLD18, [SourceSwitch.GLOBAL_MARKET]
        )
        dollar = await _asset(uow, AssetCode.USD, [SourceSwitch.IRAN_MARKET])
        ounce = await _symbol(
            uow, gold, SymbolCode.XAU_OUNCE, CurrencyType.USD
        )
        rial = await _symbol(uow, dollar, SymbolCode.USD_RIAL)
        world = await _source(
            uow, SourceCode.GOLD_API, SourceSwitch.GLOBAL_MARKET
        )
        iran = await _source(uow, SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        await _TestSourcePriceCache(redis).set_many(
            {
                SymbolCode.XAU_OUNCE: [
                    _reading(
                        400_000,
                        400_000,
                        world.id,
                        ounce.id,
                        CurrencyType.USD,
                    )
                ],
                SymbolCode.USD_RIAL: [
                    _reading(1_000_000, 1_000_000, iran.id, rial.id)
                ],
            }
        )
        service, cache = _service(uow, redis)

        # without the dollar route first, world parity has no rate to read
        empty = await service.calculate_all()
        await service.calculate_usd()
        priced = await service.calculate_all()
        found = await cache.get(AssetCode.GOLD18)

        assert empty == 0
        assert priced == 1
        assert found is not None
        assert found.price == 96_452_240

    async def test_a_sweep_with_no_asset_at_all(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        service, cache = _service(uow, redis)

        priced = await service.calculate_all()

        assert priced == 0
        assert await cache.get_all() == {}
