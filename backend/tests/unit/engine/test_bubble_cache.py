from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.results import BubbleResult
from src.modules.price.engine.infra.cache import (
    AssetPriceCache,
    BubbleCache,
    SourcePriceCache,
)
from tests.unit.engine.test_asset_price_cache import _FakeRedis


def _cache() -> tuple[BubbleCache, _FakeRedis]:
    """
    Desc: Build the cache over a fake Redis.
    Returns:
        return (tuple[BubbleCache, _FakeRedis]): The cache and its store.
    """
    fake = _FakeRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    return BubbleCache(client), fake


def _bubble(amount: int, asset_id: int = 1) -> BubbleResult:
    """
    Desc: Build a bubble to store.
    Args:
        amount (int): The premium in Rial, signed.
        asset_id (int): ID of the asset it belongs to.
    Returns:
        return (BubbleResult): The bubble.
    """
    return BubbleResult(
        asset_id=asset_id,
        amount=amount,
        priced_at=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )


class TestSetAndGet:
    async def test_a_bubble_round_trips(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _bubble(3_241_000))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == 3_241_000
        assert found.asset_id == 1

    async def test_a_negative_bubble_survives(self) -> None:
        # the market sits under world parity often enough to matter
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _bubble(-2_137_540))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == -2_137_540

    async def test_priced_at_keeps_its_timezone(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _bubble(1))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.priced_at.tzinfo is not None

    async def test_an_unset_asset_is_a_miss(self) -> None:
        cache, _ = _cache()

        found = await cache.get(AssetCode.USD)

        assert found is None

    async def test_a_second_write_replaces_the_first(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _bubble(1))
        await cache.set(AssetCode.GOLD18, _bubble(2))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == 2


class TestSetManyAndGetAll:
    async def test_it_stores_every_asset(self) -> None:
        cache, _ = _cache()

        await cache.set_many(
            {
                AssetCode.GOLD18: _bubble(1, asset_id=1),
                AssetCode.USD: _bubble(2, asset_id=2),
            }
        )
        found = await cache.get_all()

        assert {code: r.amount for code, r in found.items()} == {
            AssetCode.GOLD18: 1,
            AssetCode.USD: 2,
        }

    async def test_get_many_skips_the_misses(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, _bubble(1))

        found = await cache.get_many([AssetCode.GOLD18, AssetCode.USD])

        assert set(found) == {AssetCode.GOLD18}

    async def test_get_all_on_an_empty_cache(self) -> None:
        cache, _ = _cache()

        found = await cache.get_all()

        assert found == {}


class TestRemovalAndNamespace:
    async def test_remove_drops_one_asset_only(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, _bubble(1))
        await cache.set(AssetCode.USD, _bubble(2))

        await cache.remove(AssetCode.GOLD18)
        found = await cache.get_all()

        assert set(found) == {AssetCode.USD}

    async def test_clear_drops_everything(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, _bubble(1))

        await cache.clear()

        assert await cache.get_all() == {}

    def test_it_lives_under_the_agreed_namespace(self) -> None:
        assert BubbleCache.namespace == "bubble:price"

    def test_the_three_caches_never_share_a_namespace(self) -> None:
        # a collision would have one cache reading another's payloads
        namespaces = {
            AssetPriceCache.namespace,
            SourcePriceCache.namespace,
            BubbleCache.namespace,
        }
        assert len(namespaces) == 3

    async def test_a_bubble_does_not_land_in_the_price_namespace(
        self,
    ) -> None:
        cache, fake = _cache()

        await cache.set(AssetCode.GOLD18, _bubble(1))

        assert list(fake.store) == ["bubble:price"]
