from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

from src.infra.redis.client import RedisClient
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
from tests.unit.calculator.test_asset_price_cache import _FakeRedis

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def _service() -> tuple[CacheReaderService, AssetPriceCache, BubbleCache]:
    client = cast(RedisClient, SimpleNamespace(client=_FakeRedis()))
    prices = AssetPriceCache(client)
    bubbles = BubbleCache(client)
    return CacheReaderService(prices, bubbles), prices, bubbles


def _price(asset_id: int, price: int) -> AssetPriceResult:
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


def _bubble(asset_id: int, amount: int) -> BubbleResult:
    return BubbleResult(asset_id=asset_id, amount=amount, priced_at=_at)


class TestPrices:
    async def test_it_reads_one_asset_s_price(self) -> None:
        service, prices, _ = _service()
        await prices.set(AssetCode.GOLD18, _price(1, 100_000_000))

        found = await service.get_price(AssetCode.GOLD18)

        assert found is not None
        assert found.price == 100_000_000
        assert found.asset_id == 1

    async def test_an_asset_nobody_priced_reads_as_none(self) -> None:
        service, _, _ = _service()

        found = await service.get_price(AssetCode.GOLD18)

        assert found is None

    async def test_it_reads_every_price_there_is(self) -> None:
        service, prices, _ = _service()
        await prices.set_many(
            {
                AssetCode.GOLD18: _price(1, 100_000_000),
                AssetCode.USD: _price(2, 1_905_000),
            }
        )

        found = await service.get_all_prices()

        assert {row.asset_id: row.price for row in found} == {
            1: 100_000_000,
            2: 1_905_000,
        }

    async def test_an_empty_board_reads_empty(self) -> None:
        service, _, _ = _service()

        found = await service.get_all_prices()

        assert list(found) == []


class TestBubbles:
    async def test_it_reads_one_asset_s_premium(self) -> None:
        service, _, bubbles = _service()
        await bubbles.set(AssetCode.GOLD18, _bubble(1, -2_137_540))

        found = await service.get_bubble_amount(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == -2_137_540

    async def test_an_asset_with_no_settled_premium(self) -> None:
        service, _, _ = _service()

        found = await service.get_bubble_amount(AssetCode.GOLD18)

        assert found is None

    async def test_it_reads_every_settled_premium(self) -> None:
        service, _, bubbles = _service()
        await bubbles.set_many(
            {
                AssetCode.GOLD18: _bubble(1, 3_241_000),
                AssetCode.USD: _bubble(2, 500_000),
            }
        )

        found = await service.get_all_bubble_amounts()

        assert {row.asset_id: row.amount for row in found} == {
            1: 3_241_000,
            2: 500_000,
        }

    async def test_nothing_settled_reads_empty(self) -> None:
        service, _, _ = _service()

        found = await service.get_all_bubble_amounts()

        assert list(found) == []
