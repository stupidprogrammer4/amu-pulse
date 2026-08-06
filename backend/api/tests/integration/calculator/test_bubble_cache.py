from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from redis.exceptions import RedisError

from src.core.config import Settings
from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import BubbleResult
from src.modules.price.calculator.infra.cache import BubbleCache


class _TestBubbleCache(BubbleCache):
    namespace = "test:bubble:price"


@pytest.fixture
async def cache(
    integration_settings: Settings,
) -> AsyncIterator[_TestBubbleCache]:
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
    built = _TestBubbleCache(client)
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


def _bubble(amount: int, asset_id: int = 1) -> BubbleResult:
    return BubbleResult(
        asset_id=asset_id,
        amount=amount,
        priced_at=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )


class TestBubbleCacheAgainstRedis:
    async def test_a_negative_bubble_round_trips(
        self, cache: _TestBubbleCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _bubble(-2_137_540))

        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == -2_137_540
        assert found.priced_at.tzinfo is not None

    async def test_both_assets_come_back_in_one_read(
        self, cache: _TestBubbleCache
    ) -> None:
        await cache.set_many(
            {
                AssetCode.GOLD18: _bubble(-2_137_540, asset_id=1),
                AssetCode.USD: _bubble(500_000, asset_id=2),
            }
        )

        found = await cache.get_all()

        assert {code: r.amount for code, r in found.items()} == {
            AssetCode.GOLD18: -2_137_540,
            AssetCode.USD: 500_000,
        }

    async def test_it_really_is_one_hash(
        self, cache: _TestBubbleCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _bubble(1))

        kind = await cache.redis.client.type(cache.namespace)

        assert kind == "hash"

    async def test_clear_empties_the_namespace(
        self, cache: _TestBubbleCache
    ) -> None:
        await cache.set(AssetCode.GOLD18, _bubble(1))

        await cache.clear()

        assert await cache.get_all() == {}
