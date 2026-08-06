from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from redis.exceptions import RedisError

from src.core.config import Settings
from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.calculator.infra.cache import AssetPriceCache


class _TestAssetPriceCache(AssetPriceCache):
    namespace = "test:assets:price"


@pytest.fixture
async def cache(
    integration_settings: Settings,
) -> AsyncIterator[_TestAssetPriceCache]:
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
    built = _TestAssetPriceCache(client)
    try:
        await client.client.ping()
    except (RedisError, OSError) as exc:
        await client.close()
        pytest.skip(f"redis is not reachable: {exc}")
    try:
        await built.clear()
        yield built
    finally:
        await built.clear()
        await client.close()


def _result(price: int, asset_id: int = 1) -> AssetPriceResult:
    return AssetPriceResult(
        asset_id=asset_id,
        buy_price=price - 1000,
        sell_price=price + 1000,
        price=price,
        buy_spread=1000,
        sell_spread=1000,
        buy_spread_rate=0.00125,
        sell_spread_rate=0.00125,
        priced_at=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )


class TestAssetPriceCacheAgainstRedis:
    async def test_a_price_round_trips_through_redis(
        self, cache: _TestAssetPriceCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _result(185_820_000))

        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.price == 185_820_000
        assert found.buy_spread_rate == 0.00125
        assert found.priced_at.tzinfo is not None

    async def test_the_whole_board_comes_back_in_one_read(
        self, cache: _TestAssetPriceCache
    ) -> None:
        await cache.set_many(
            {
                AssetCode.GOLD18: _result(185_820_000, asset_id=1),
                AssetCode.USD: _result(1_931_900, asset_id=2),
            }
        )

        found = await cache.get_all()

        assert {code: r.price for code, r in found.items()} == {
            AssetCode.GOLD18: 185_820_000,
            AssetCode.USD: 1_931_900,
        }

    async def test_it_really_is_one_hash(
        self, cache: _TestAssetPriceCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _result(1))

        kind = await cache.redis.client.type(cache.namespace)

        assert kind == "hash"

    async def test_remove_leaves_the_other_assets_alone(
        self, cache: _TestAssetPriceCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _result(1))
        await cache.set(AssetCode.USD, _result(2))

        await cache.remove(AssetCode.GOLD18)
        found = await cache.get_all()

        assert set(found) == {AssetCode.USD}

    async def test_clear_empties_the_namespace(
        self, cache: _TestAssetPriceCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _result(1))

        await cache.clear()

        assert await cache.get_all() == {}
