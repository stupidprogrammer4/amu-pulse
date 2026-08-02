from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from redis.exceptions import RedisError

from src.core.config import Settings
from src.infra.redis.client import RedisClient, resolve
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.app.services import CacheReaderService
from src.modules.price.calculator.domain.results import (
    AssetPriceResult,
    BubbleResult,
)
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


class _TestAssetPriceCache(AssetPriceCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:reader:assets:price"


class _TestBubbleCache(BubbleCache):
    namespace = "test:reader:bubble:price"


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
    caches = (_TestAssetPriceCache(client), _TestBubbleCache(client))
    for cache in caches:
        await cache.clear()
    try:
        yield client
    finally:
        for cache in caches:
            await cache.clear()
        await client.close()


def _service(
    redis: RedisClient,
) -> tuple[CacheReaderService, _TestAssetPriceCache, _TestBubbleCache]:
    """
    Desc: Build the service over the real caches.
    Args:
        redis (RedisClient): Client both caches run on.
    Returns:
        return (tuple[CacheReaderService, _TestAssetPriceCache,
            _TestBubbleCache]): The service and the two caches it reads.
    """
    prices = _TestAssetPriceCache(redis)
    bubbles = _TestBubbleCache(redis)
    return CacheReaderService(prices, bubbles), prices, bubbles


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


class TestCacheReaderServiceAgainstRedis:
    async def test_a_price_round_trips_through_redis(
        self, redis: RedisClient
    ) -> None:
        service, prices, _ = _service(redis)
        await prices.set(AssetCode.GOLD18, _price(1, 100_000_000))

        found = await service.get_price(AssetCode.GOLD18)

        assert found is not None
        assert found.price == 100_000_000
        assert found.priced_at.tzinfo is not None

    async def test_a_negative_premium_round_trips(
        self, redis: RedisClient
    ) -> None:
        service, _, bubbles = _service(redis)
        await bubbles.set(
            AssetCode.GOLD18,
            BubbleResult(asset_id=1, amount=-2_137_540, priced_at=_at),
        )

        found = await service.get_bubble_amount(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == -2_137_540

    async def test_it_reads_the_whole_board_in_one_call(
        self, redis: RedisClient
    ) -> None:
        service, prices, bubbles = _service(redis)
        await prices.set_many(
            {
                AssetCode.GOLD18: _price(1, 100_000_000),
                AssetCode.USD: _price(2, 1_905_000),
            }
        )
        await bubbles.set(
            AssetCode.GOLD18,
            BubbleResult(asset_id=1, amount=3_241_000, priced_at=_at),
        )

        found_prices = await service.get_all_prices()
        found_bubbles = await service.get_all_bubble_amounts()

        assert {row.price for row in found_prices} == {
            100_000_000,
            1_905_000,
        }
        assert [row.amount for row in found_bubbles] == [3_241_000]

    async def test_an_empty_cache_reads_empty(
        self, redis: RedisClient
    ) -> None:
        service, _, _ = _service(redis)

        assert await service.get_price(AssetCode.GOLD18) is None
        assert await service.get_bubble_amount(AssetCode.GOLD18) is None
        assert list(await service.get_all_prices()) == []
        assert list(await service.get_all_bubble_amounts()) == []
