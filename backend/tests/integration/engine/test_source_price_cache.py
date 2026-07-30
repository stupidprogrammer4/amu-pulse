from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from redis.exceptions import RedisError

from src.core.config import Settings
from src.infra.redis.client import RedisClient
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.engine.infra.cache import SourcePriceCache
from src.modules.price.symbols.domain.enums import SymbolCode


class _TestSourcePriceCache(SourcePriceCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:sources:price"


@pytest.fixture
async def cache(
    integration_settings: Settings,
) -> AsyncIterator[_TestSourcePriceCache]:
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
    built = _TestSourcePriceCache(client)
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


def _reading(source_id: int, price: int) -> SourcePriceResult:
    """
    Desc: Build one source's reading for an asset.
    Args:
        source_id (int): ID of the source that quoted it.
        price (int): The mid price in Rial.
    Returns:
        return (SourcePriceResult): The reading.
    """
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=1,
        buy_price=price - 1000,
        sell_price=price + 1000,
        price=price,
        buy_spread_rial=1000,
        sell_spread_rial=1000,
        buy_spread_rate=Decimal("0.00125"),
        sell_spread_rate=Decimal("0.00125"),
        priced_at=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )


class TestSourcePriceCacheAgainstRedis:
    async def test_a_readings_list_round_trips(
        self, cache: _TestSourcePriceCache
    ) -> None:
        await cache.set(
            SymbolCode.GOLD18_GRAM,
            [_reading(1, 185_820_000), _reading(2, 187_455_000)],
        )

        found = await cache.get(SymbolCode.GOLD18_GRAM)

        assert found is not None
        assert [r.source_id for r in found] == [1, 2]
        assert found[0].buy_spread_rate == Decimal("0.00125")
        assert found[0].priced_at.tzinfo is not None

    async def test_both_symbols_come_back_in_one_read(
        self, cache: _TestSourcePriceCache
    ) -> None:
        await cache.set_many(
            {
                SymbolCode.GOLD18_GRAM: [_reading(1, 185_820_000)],
                SymbolCode.USD_RIAL: [
                    _reading(2, 1_931_900),
                    _reading(3, 1_934_030),
                ],
            }
        )

        found = await cache.get_all()

        assert {code: len(rows) for code, rows in found.items()} == {
            SymbolCode.GOLD18_GRAM: 1,
            SymbolCode.USD_RIAL: 2,
        }

    async def test_it_really_is_one_hash(
        self, cache: _TestSourcePriceCache
    ) -> None:
        await cache.set(SymbolCode.GOLD18_GRAM, [_reading(1, 1)])

        kind = await cache.redis.client.type(cache.namespace)

        assert kind == "hash"

    async def test_remove_leaves_the_other_asset_alone(
        self, cache: _TestSourcePriceCache
    ) -> None:
        await cache.set(SymbolCode.GOLD18_GRAM, [_reading(1, 1)])
        await cache.set(SymbolCode.USD_RIAL, [_reading(2, 2)])

        await cache.remove(SymbolCode.GOLD18_GRAM)
        found = await cache.get_all()

        assert set(found) == {SymbolCode.USD_RIAL}
