from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, Sequence, cast

from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.results import AssetPriceResult
from src.modules.price.engine.infra.cache import AssetPriceCache


class _FakeRedis:
    """The handful of hash commands the cache uses, over a dict."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, str]] = {}

    async def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict[str, str] | None = None,
    ) -> int:
        hash_ = self.store.setdefault(name, {})
        if mapping is not None:
            hash_.update(mapping)
        if key is not None and value is not None:
            hash_[key] = value
        return 1

    async def hget(self, name: str, key: str) -> str | None:
        return self.store.get(name, {}).get(key)

    async def hmget(self, name: str, keys: Sequence[str]) -> list[str | None]:
        hash_ = self.store.get(name, {})
        return [hash_.get(key) for key in keys]

    async def hgetall(self, name: str) -> dict[str, str]:
        return dict(self.store.get(name, {}))

    async def hdel(self, name: str, *keys: str) -> int:
        hash_ = self.store.get(name, {})
        for key in keys:
            hash_.pop(key, None)
        return 1

    async def delete(self, *names: str) -> int:
        for name in names:
            self.store.pop(name, None)
        return 1


def _cache() -> tuple[AssetPriceCache, _FakeRedis]:
    """
    Desc: Build the cache over a fake Redis.
    Returns:
        return (tuple[AssetPriceCache, _FakeRedis]): The cache and its store.
    """
    fake = _FakeRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    return AssetPriceCache(client), fake


def _result(price: int, asset_id: int = 1) -> AssetPriceResult:
    """
    Desc: Build a priced result to store.
    Args:
        price (int): The mid price in Rial.
        asset_id (int): ID of the asset it belongs to.
    Returns:
        return (AssetPriceResult): The result.
    """
    return AssetPriceResult(
        asset_id=asset_id,
        buy_price=price - 1000,
        sell_price=price + 1000,
        price=price,
        buy_spread=1000,
        sell_spread=1000,
        buy_spread_rate=0.001,
        sell_spread_rate=0.001,
        priced_at=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )


class TestSetAndGet:
    async def test_a_stored_price_round_trips(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _result(185_000_000))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.price == 185_000_000
        assert found.asset_id == 1

    async def test_the_spread_rate_survives_the_round_trip(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _result(1))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.buy_spread_rate == 0.001

    async def test_priced_at_keeps_its_timezone(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _result(1))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.priced_at.tzinfo is not None

    async def test_an_unset_asset_is_a_miss(self) -> None:
        cache, _ = _cache()

        found = await cache.get(AssetCode.USD)

        assert found is None

    async def test_a_second_write_replaces_the_first(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, _result(1))
        await cache.set(AssetCode.GOLD18, _result(2))
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.price == 2

    async def test_every_asset_gets_its_own_field(self) -> None:
        cache, fake = _cache()

        await cache.set(AssetCode.GOLD18, _result(1))
        await cache.set(AssetCode.USD, _result(2))

        assert set(fake.store[AssetPriceCache.namespace]) == {"gold18", "usd"}


class TestSetMany:
    async def test_it_stores_every_asset(self) -> None:
        cache, _ = _cache()

        await cache.set_many(
            {AssetCode.GOLD18: _result(1), AssetCode.USD: _result(2)}
        )
        found = await cache.get_all()

        assert {code: r.price for code, r in found.items()} == {
            AssetCode.GOLD18: 1,
            AssetCode.USD: 2,
        }


class TestGetManyAndAll:
    async def test_get_many_skips_the_misses(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, _result(1))

        found = await cache.get_many([AssetCode.GOLD18, AssetCode.USD])

        assert set(found) == {AssetCode.GOLD18}

    async def test_get_all_on_an_empty_cache(self) -> None:
        cache, _ = _cache()

        found = await cache.get_all()

        assert found == {}


class TestRemoval:
    async def test_remove_drops_one_asset_only(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, _result(1))
        await cache.set(AssetCode.USD, _result(2))

        await cache.remove(AssetCode.GOLD18)
        found = await cache.get_all()

        assert set(found) == {AssetCode.USD}

    async def test_clear_drops_the_whole_board(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, _result(1))

        await cache.clear()
        found = await cache.get_all()

        assert found == {}

    async def test_removing_a_missing_asset_is_harmless(self) -> None:
        cache, _ = _cache()

        await cache.remove(AssetCode.GOLD18)

        assert await cache.get(AssetCode.GOLD18) is None


class TestNamespace:
    def test_it_lives_under_the_agreed_namespace(self) -> None:
        assert AssetPriceCache.namespace == "assets:price"

    async def test_nothing_is_written_outside_it(self) -> None:
        cache, fake = _cache()

        await cache.set(AssetCode.GOLD18, _result(1))

        assert list(fake.store) == ["assets:price"]

    async def test_the_field_is_the_asset_code(self) -> None:
        cache, fake = _cache()

        await cache.set(AssetCode.GOLD18, _result(1))

        stored: dict[str, Any] = fake.store["assets:price"]
        assert "gold18" in stored
