from datetime import UTC, datetime
from typing import Any, Sequence, cast

import pytest

import src.tasks.broker  # noqa: F401
from src.common.errors.exceptions import NotFoundException
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.schemas import (
    AssetPriceOut,
    RepriceOut,
)
from src.modules.price.assets.routers import admin
from src.modules.price.calculator.domain.results import (
    AssetPriceResult,
    BubbleResult,
)
from src.modules.price.calculator.interfaces import ICacheReaderService

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


class _FakeCacheReader:
    """The one read the price route makes."""

    def __init__(self, price: AssetPriceResult | None) -> None:
        self.price = price
        self.asked: list[AssetCode] = []

    async def get_price(
        self, asset_code: AssetCode
    ) -> AssetPriceResult | None:
        self.asked.append(asset_code)
        return self.price

    async def get_bubble_amount(
        self, bubble_code: AssetCode
    ) -> BubbleResult | None:
        return None

    async def get_all_bubble_amounts(self) -> Sequence[BubbleResult]:
        return []

    async def get_all_prices(self) -> Sequence[AssetPriceResult]:
        return []


class _FakeJob:
    """What kiq answers with once the job is queued."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class _FakeTask:
    """The reprice task, kicked but never run."""

    def __init__(self) -> None:
        self.kicked: list[Any] = []

    async def kiq(self, code: AssetCode) -> _FakeJob:
        self.kicked.append(code)
        return _FakeJob("job-1")


def _price(asset_id: int = 1, price: int = 100_500_000) -> AssetPriceResult:
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
        buy_price=100_000_000,
        sell_price=101_000_000,
        price=price,
        buy_spread=500_000,
        sell_spread=500_000,
        buy_spread_rate=0.005,
        sell_spread_rate=0.005,
        priced_at=_at,
    )


class TestGetAssetPrice:
    async def test_it_answers_with_what_the_cache_holds(self) -> None:
        reader = _FakeCacheReader(_price())

        response = await admin.get_asset_price(
            AssetCode.GOLD18, cast(ICacheReaderService, reader)
        )

        data = cast(AssetPriceOut, response.data)

        assert response.success is True
        assert data.price == 100_500_000
        assert reader.asked == [AssetCode.GOLD18]

    async def test_the_asset_id_leaves_encoded(self) -> None:
        reader = _FakeCacheReader(_price(asset_id=7))

        response = await admin.get_asset_price(
            AssetCode.GOLD18, cast(ICacheReaderService, reader)
        )
        dumped = response.model_dump()

        assert dumped["data"]["asset_id"] == ASSET_ID_ENCRYPTION.encode(7)

    async def test_an_asset_nobody_priced_is_a_not_found(self) -> None:
        reader = _FakeCacheReader(None)

        with pytest.raises(NotFoundException):
            await admin.get_asset_price(
                AssetCode.USD, cast(ICacheReaderService, reader)
            )


class TestRepriceAsset:
    async def test_it_answers_with_the_job_it_queued(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        task = _FakeTask()
        monkeypatch.setattr(admin, "reprice", task)

        response = await admin.reprice_asset(AssetCode.GOLD18)

        data = cast(RepriceOut, response.data)

        assert response.success is True
        assert data.task_id == "job-1"

    async def test_the_asset_asked_for_is_the_one_queued(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        task = _FakeTask()
        monkeypatch.setattr(admin, "reprice", task)

        await admin.reprice_asset(AssetCode.USD)

        assert task.kicked == [AssetCode.USD]
