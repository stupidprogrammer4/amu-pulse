from datetime import datetime
from types import SimpleNamespace
from typing import cast

from src.common.utils import date_utils
from src.infra.redis.client import RedisClient
from src.modules.chart.candle.app.services import WindowService
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.infra.cache import AssetWindowCache
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import AssetPriceResult
from tests.unit.candle.test_window_caches import _FakeWindowRedis


def _service() -> tuple[WindowService, AssetWindowCache]:
    fake = _FakeWindowRedis()
    client = cast(RedisClient, SimpleNamespace(client=fake))
    cache = AssetWindowCache(client)
    return WindowService(cache), cache


def _priced(
    price: int,
    asset_id: int = 1,
    priced_at: datetime | None = None,
) -> AssetPriceResult:
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


def _opened_now() -> int:
    stamp = int(date_utils.utc_now().timestamp())
    return TimeFrame.FIVE_MINUTE.opened_at(stamp)


class TestFoldingOneAssetsPrice:
    async def test_the_first_price_opens_the_window_flat(self) -> None:
        service, cache = _service()

        folded = await service.update_window(AssetCode.GOLD18, _priced(100))

        window = await cache.get(_opened_now(), AssetCode.GOLD18)
        assert folded is True
        assert window is not None
        assert (window.open, window.high, window.low, window.close) == (
            100,
            100,
            100,
            100,
        )

    async def test_the_next_price_folds_into_the_standing_window(
        self,
    ) -> None:
        service, cache = _service()

        await service.update_window(AssetCode.GOLD18, _priced(100))
        await service.update_window(AssetCode.GOLD18, _priced(140))
        await service.update_window(AssetCode.GOLD18, _priced(90))

        window = await cache.get(_opened_now(), AssetCode.GOLD18)
        assert window is not None
        assert (window.open, window.high, window.low, window.close) == (
            100,
            140,
            90,
            90,
        )

    async def test_the_price_lands_under_the_window_it_was_priced_in(
        self,
    ) -> None:
        service, cache = _service()

        await service.update_window(AssetCode.GOLD18, _priced(100))

        assert await cache.get_all(_opened_now()) != {}

    async def test_each_asset_keeps_a_window_of_its_own(self) -> None:
        service, cache = _service()

        await service.update_window(AssetCode.GOLD18, _priced(100, 1))
        await service.update_window(AssetCode.USD, _priced(1_900, 2))

        windows = await cache.get_all(_opened_now())
        assert {code: row.close for code, row in windows.items()} == {
            AssetCode.GOLD18: 100,
            AssetCode.USD: 1_900,
        }

    async def test_every_price_is_folded_in_one_go(self) -> None:
        service, cache = _service()

        count = await service.update_windows(
            {
                AssetCode.GOLD18: _priced(100, 1),
                AssetCode.USD: _priced(1_900, 2),
            }
        )

        windows = await cache.get_all(_opened_now())
        assert count == 2
        assert {code: row.asset_id for code, row in windows.items()} == {
            AssetCode.GOLD18: 1,
            AssetCode.USD: 2,
        }

    async def test_a_second_sweep_folds_into_the_standing_windows(
        self,
    ) -> None:
        service, cache = _service()

        await service.update_windows({AssetCode.GOLD18: _priced(100)})
        await service.update_windows({AssetCode.GOLD18: _priced(140)})

        window = await cache.get(_opened_now(), AssetCode.GOLD18)
        assert window is not None
        assert (window.open, window.high, window.close) == (100, 140, 140)

    async def test_a_sweep_folds_onto_what_a_single_price_opened(
        self,
    ) -> None:
        service, cache = _service()

        await service.update_window(AssetCode.GOLD18, _priced(100))
        await service.update_windows({AssetCode.GOLD18: _priced(90)})

        window = await cache.get(_opened_now(), AssetCode.GOLD18)
        assert window is not None
        assert (window.open, window.low, window.close) == (100, 90, 90)

    async def test_a_sweep_that_priced_nothing_folds_nothing(self) -> None:
        service, cache = _service()

        count = await service.update_windows({})

        assert count == 0
        assert await cache.get_all(_opened_now()) == {}
