from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.engine.infra.cache import SourcePriceCache
from tests.unit.engine.test_asset_price_cache import _FakeRedis


def _cache() -> tuple[SourcePriceCache, _FakeRedis]:
    """
    Desc: Build the cache over a fake Redis.
    Returns:
        return (tuple[SourcePriceCache, _FakeRedis]): Cache and its store.
    """
    fake = _FakeRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    return SourcePriceCache(client), fake


def _reading(
    source_id: int,
    price: int,
    asset_id: int = 1,
) -> SourcePriceResult:
    """
    Desc: Build one source's reading for an asset.
    Args:
        source_id (int): ID of the source that quoted it.
        price (int): The mid price in Rial.
        asset_id (int): ID of the asset priced.
    Returns:
        return (SourcePriceResult): The reading.
    """
    return SourcePriceResult(
        source_id=source_id,
        asset_id=asset_id,
        buy_price=price - 1000,
        sell_price=price + 1000,
        price=price,
        buy_spread_rial=1000,
        sell_spread_rial=1000,
        buy_spread_rate=Decimal("0.00125"),
        sell_spread_rate=Decimal("0.00125"),
        priced_at=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )


class TestSetAndGet:
    async def test_every_source_for_an_asset_round_trips(self) -> None:
        cache, _ = _cache()
        readings = [_reading(1, 185_000_000), _reading(2, 186_000_000)]

        await cache.set(AssetCode.GOLD18, readings)
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert [r.source_id for r in found] == [1, 2]
        assert [r.price for r in found] == [185_000_000, 186_000_000]

    async def test_the_decimal_spread_survives_the_round_trip(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found[0].buy_spread_rate == Decimal("0.00125")

    async def test_the_source_order_is_kept(self) -> None:
        # the aggregation reads positionally when it picks a median
        cache, _ = _cache()
        readings = [_reading(i, i * 1000) for i in (5, 2, 9)]

        await cache.set(AssetCode.GOLD18, readings)
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert [r.source_id for r in found] == [5, 2, 9]

    async def test_an_unset_asset_is_a_miss(self) -> None:
        cache, _ = _cache()

        found = await cache.get(AssetCode.USD)

        assert found is None

    async def test_an_empty_reading_list_is_not_a_miss(self) -> None:
        # every source failing is a real answer, distinct from never fetched
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, [])
        found = await cache.get(AssetCode.GOLD18)

        assert found == []

    async def test_a_second_write_replaces_the_whole_list(self) -> None:
        cache, _ = _cache()

        await cache.set(AssetCode.GOLD18, [_reading(1, 1), _reading(2, 2)])
        await cache.set(AssetCode.GOLD18, [_reading(3, 3)])
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert [r.source_id for r in found] == [3]


class TestSetMany:
    async def test_it_stores_every_asset(self) -> None:
        cache, _ = _cache()

        await cache.set_many(
            {
                AssetCode.GOLD18: [_reading(1, 1), _reading(2, 2)],
                AssetCode.USD: [_reading(1, 3, asset_id=2)],
            }
        )
        found = await cache.get_all()

        assert {code: len(rows) for code, rows in found.items()} == {
            AssetCode.GOLD18: 2,
            AssetCode.USD: 1,
        }

    async def test_an_empty_pass_writes_nothing(self) -> None:
        cache, fake = _cache()

        await cache.set_many({})

        assert fake.store == {}


class TestGetManyAndAll:
    async def test_get_many_skips_the_misses(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])

        found = await cache.get_many([AssetCode.GOLD18, AssetCode.USD])

        assert set(found) == {AssetCode.GOLD18}

    async def test_get_many_with_no_codes_reads_nothing(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])

        found = await cache.get_many([])

        assert found == {}

    async def test_get_all_on_an_empty_cache(self) -> None:
        cache, _ = _cache()

        found = await cache.get_all()

        assert found == {}


class TestBadPayloads:
    async def test_a_corrupt_payload_reads_as_a_miss(self) -> None:
        cache, fake = _cache()
        fake.store[SourcePriceCache.namespace] = {"gold18": "[{}]"}

        found = await cache.get(AssetCode.GOLD18)

        assert found is None

    async def test_a_bare_object_is_a_miss_not_a_list(self) -> None:
        # the field holds a list; a single object left by an older shape
        # must not slip through as one reading
        cache, fake = _cache()
        stored = SourcePriceCache.adapter.dump_json([_reading(1, 1)]).decode()
        fake.store[SourcePriceCache.namespace] = {"gold18": stored[1:-1]}

        found = await cache.get(AssetCode.GOLD18)

        assert found is None

    async def test_get_all_drops_a_field_that_is_not_an_asset(self) -> None:
        cache, fake = _cache()
        await cache.set(AssetCode.USD, [_reading(1, 1)])
        stored = fake.store[SourcePriceCache.namespace]["usd"]
        fake.store[SourcePriceCache.namespace]["gold24"] = stored

        found = await cache.get_all()

        assert set(found) == {AssetCode.USD}


class TestRemovalAndNamespace:
    async def test_remove_drops_one_asset_only(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])
        await cache.set(AssetCode.USD, [_reading(2, 2)])

        await cache.remove(AssetCode.GOLD18)
        found = await cache.get_all()

        assert set(found) == {AssetCode.USD}

    async def test_clear_drops_everything(self) -> None:
        cache, _ = _cache()
        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])

        await cache.clear()

        assert await cache.get_all() == {}

    def test_it_lives_under_the_agreed_namespace(self) -> None:
        assert SourcePriceCache.namespace == "sources:price"

    async def test_it_does_not_share_the_asset_price_namespace(self) -> None:
        cache, fake = _cache()

        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])

        assert list(fake.store) == ["sources:price"]

    async def test_the_field_is_the_asset_code(self) -> None:
        cache, fake = _cache()

        await cache.set(AssetCode.GOLD18, [_reading(1, 1)])

        assert "gold18" in fake.store["sources:price"]
