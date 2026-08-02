from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.calculator.domain.results import AssetPriceResult
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from tests.api.conftest import (
    ApiAssetPriceCache,
    ApiSourcePriceCache,
)
from tests.conftest import NullScheduler

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset with its default config.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(AssetCreate(title="طلا", code=code))
    return asset


def _price(asset_id: int, price: int = 100_500_000) -> AssetPriceResult:
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


def _reading(source_id: int, price: int) -> SourcePriceResult:
    """
    Desc: Build one cached source reading.
    Args:
        source_id (int): ID of the source that quoted it.
        price (int): The mid price in rial.
    Returns:
        return (SourcePriceResult): The reading.
    """
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=1,
        currency=CurrencyType.RIAL,
        buy_price=price,
        sell_price=price,
        price=price,
        buy_spread=0,
        sell_spread=0,
        buy_spread_rate=0.0,
        sell_spread_rate=0.0,
        priced_at=_at,
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestGetAssetPrice:
    async def test_it_serves_what_the_calculator_cached(
        self, client: AsyncClient, caches: RedisClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await ApiAssetPriceCache(caches).set(
            AssetCode.GOLD18, _price(asset.id)
        )

        response = await client.get("/assets/gold18/price")
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["price"] == 100_500_000
        assert body["data"]["asset_id"] == ASSET_ID_ENCRYPTION.encode(asset.id)

    async def test_an_asset_nobody_priced_answers_404(
        self, client: AsyncClient, caches: RedisClient
    ) -> None:
        response = await client.get("/assets/gold18/price")

        assert response.status_code == 404
        assert response.json()["success"] is False

    async def test_a_code_that_is_not_an_asset_answers_422(
        self, client: AsyncClient, caches: RedisClient
    ) -> None:
        response = await client.get("/assets/platinum/price")

        assert response.status_code == 422


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestRepriceAsset:
    async def test_it_answers_with_the_job_it_queued(
        self, client: AsyncClient, caches: RedisClient, queue: str
    ) -> None:
        response = await client.post("/assets/gold18/reprice")
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["task_id"]

    async def test_the_price_is_not_what_it_answers(
        self, client: AsyncClient, caches: RedisClient, queue: str
    ) -> None:
        # the job is the answer; the price lands in the cache later
        response = await client.post("/assets/usd/reprice")

        assert "price" not in response.json()["data"]


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestGetSourcePrices:
    async def test_it_serves_the_whole_board(
        self, client: AsyncClient, caches: RedisClient
    ) -> None:
        await ApiSourcePriceCache(caches).set_many(
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(12, 100_000_000),
                    _reading(13, 101_000_000),
                ],
                SymbolCode.USD_RIAL: [_reading(12, 1_900_000)],
            }
        )

        response = await client.get("/sources/prices")
        body = response.json()

        assert response.status_code == 200
        assert {row["symbol"] for row in body["data"]} == {
            "gold18_gram",
            "usd_rial",
        }
        assert {len(row["prices"]) for row in body["data"]} == {2, 1}

    async def test_the_source_id_is_served_encoded(
        self, client: AsyncClient, caches: RedisClient
    ) -> None:
        await ApiSourcePriceCache(caches).set(
            SymbolCode.GOLD18_GRAM, [_reading(12, 100_000_000)]
        )

        response = await client.get("/sources/prices")
        body = response.json()

        assert body["data"][0]["prices"][0][
            "source_id"
        ] == SOURCE_ID_ENCRYPTION.encode(12)

    async def test_a_board_the_crawl_never_filled(
        self, client: AsyncClient, caches: RedisClient
    ) -> None:
        response = await client.get("/sources/prices")

        assert response.status_code == 200
        assert response.json()["data"] == []
