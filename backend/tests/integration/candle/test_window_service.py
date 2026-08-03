from collections.abc import AsyncIterator
from datetime import datetime

import pytest
from redis.exceptions import RedisError

from src.common.utils import date_utils
from src.core.config import Settings
from src.infra.redis.client import RedisClient, resolve
from src.modules.chart.candle.app.services import WindowService
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.infra.cache import AssetWindowCache
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import AssetPriceResult


class _TestAssetWindowCache(AssetWindowCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:assets:window"


def _opened_now() -> int:
    """
    Desc: Read when the window prices are folded into opened at.
    Returns:
        return (int): The moment it opened, in whole seconds.
    """
    stamp = int(date_utils.utc_now().timestamp())
    return TimeFrame.FIVE_MINUTE.opened_at(stamp)


@pytest.fixture
async def cache(
    integration_settings: Settings,
) -> AsyncIterator[_TestAssetWindowCache]:
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
    built = _TestAssetWindowCache(client)
    try:
        # reaching redis at all is what decides whether these can run
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        await client.close()
        pytest.skip(f"redis is not reachable: {exc}")
    try:
        await built.remove(_opened_now())
        yield built
    finally:
        await built.remove(_opened_now())
        await client.close()


def _priced(
    price: int,
    asset_id: int = 1,
    priced_at: datetime | None = None,
) -> AssetPriceResult:
    """
    Desc: Build what an asset was priced at, now unless told otherwise.
    Args:
        price (int): The mid price in rial.
        asset_id (int): ID of the asset it belongs to.
        priced_at (datetime | None): When it was priced, or now.
    Returns:
        return (AssetPriceResult): The price.
    """
    return AssetPriceResult(
        asset_id=asset_id,
        buy_price=price - 1_000,
        sell_price=price + 1_000,
        price=price,
        buy_spread=1_000,
        sell_spread=1_000,
        buy_spread_rate=0.1,
        sell_spread_rate=0.1,
        priced_at=priced_at or date_utils.utc_now(),
    )


class TestTheWindowServiceOverRedis:
    async def test_a_sweep_of_prices_folds_into_one_window(
        self, cache: _TestAssetWindowCache
    ) -> None:
        service = WindowService(cache)

        await service.update_windows(
            {
                AssetCode.GOLD18: _priced(100, 1),
                AssetCode.USD: _priced(1_900, 2),
            }
        )
        await service.update_windows(
            {
                AssetCode.GOLD18: _priced(140, 1),
                AssetCode.USD: _priced(1_800, 2),
            }
        )

        windows = await cache.get_all(_opened_now())
        gold = windows[AssetCode.GOLD18]
        usd = windows[AssetCode.USD]
        assert (gold.open, gold.high, gold.close) == (100, 140, 140)
        assert (usd.open, usd.low, usd.close) == (1_900, 1_800, 1_800)

    async def test_a_single_price_folds_onto_what_a_sweep_left(
        self, cache: _TestAssetWindowCache
    ) -> None:
        service = WindowService(cache)

        await service.update_windows({AssetCode.GOLD18: _priced(100)})
        folded = await service.update_window(AssetCode.GOLD18, _priced(90))

        window = await cache.get(_opened_now(), AssetCode.GOLD18)
        assert folded is True
        assert window is not None
        assert (window.open, window.low, window.close) == (100, 90, 90)

    async def test_the_window_expires_on_its_own(
        self, cache: _TestAssetWindowCache
    ) -> None:
        # nothing is left behind when no flusher comes for it
        service = WindowService(cache)

        await service.update_window(AssetCode.GOLD18, _priced(100))

        key = f"{cache.namespace}:{_opened_now()}"
        left = await cache.redis.client.ttl(key)
        assert 0 < left <= cache.ttl
