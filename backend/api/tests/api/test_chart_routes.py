import pytest
from httpx import AsyncClient

from src.common.utils import date_utils
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
)
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
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.config.constants import SYMBOL_ID_ENCRYPTION
from src.modules.price.symbols.domain.dtos import SymbolCreate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.domain.models import SymbolModel
from src.modules.price.symbols.infra.repository import SymbolRepository
from tests.conftest import NullScheduler

_minute = 60


def _now() -> int:
    """
    Desc: Read the moment the charts are measured back from.
    Returns:
        return (int): Now, in whole seconds.
    """
    return int(date_utils.utc_now().timestamp())


async def _asset(uow: PGUnitOfWork) -> AssetModel:
    """
    Desc: Create one asset to chart.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (AssetModel): The created asset.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(
        AssetCreate(
            title="طلا",
            code=AssetCode.GOLD18,
            primary_color="#c8a44b",
        )
    )
    return asset


async def _symbol(uow: PGUnitOfWork, asset: AssetModel) -> SymbolModel:
    """
    Desc: Create the line the asset is quoted through.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the line belongs to.
    Returns:
        return (SymbolModel): The created line.
    """
    symbols = SymbolService(SymbolRepository(uow))
    symbol = await symbols.create(
        SymbolCreate(
            title="هر گرم",
            code=SymbolCode.GOLD18_GRAM,
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=CurrencyType.RIAL,
            primary_color="#c8a44b",
        )
    )
    return symbol


async def _source(uow: PGUnitOfWork) -> SourceModel:
    """
    Desc: Create one source that quotes the line.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (SourceModel): The created source.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    sources = SourceService(SourceRepository(uow), configs)
    source = await sources.create(
        SourceCreate(
            title="منبع",
            code=SourceCode.TGJU,
            website_url="https://example.test",
            icon_url="/storage/file/ab/x.png",
            primary_color="#4b8ec8",
            source_type=SourceSwitch.IRAN_MARKET,
        )
    )
    return source


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheAssetChartRoute:
    async def test_it_serves_the_points_and_the_move(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await PriceTickerRepository(uow).bulk_create(
            [
                PriceTickerModel(
                    asset_id=asset.id,
                    price=price,
                    timestamp=now - stamp * _minute,
                )
                for stamp, price in [(10, 100), (5, 120)]
            ]
        )
        await uow.commit()

        response = await client.get(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/chart",
            params={"type": "daily"},
        )
        body = response.json()

        assert response.status_code == 200
        assert [p["price"] for p in body["data"]["points"]] == [100, 120]
        assert body["data"]["change_rate"] == pytest.approx(0.2)
        assert body["data"]["max"] == 120

    async def test_the_charted_asset_comes_back_named(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await PriceTickerRepository(uow).bulk_create(
            [PriceTickerModel(asset_id=asset.id, price=100, timestamp=now)]
        )
        await uow.commit()

        response = await client.get(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/chart",
            params={"type": "daily"},
        )
        body = response.json()

        assert body["meta"]["assets"][0]["code"] == "gold18"
        assert body["meta"]["assets"][0]["primary_color"] == "#c8a44b"
        assert body["meta"]["assets"][0]["id"] == ASSET_ID_ENCRYPTION.encode(
            asset.id
        )

    async def test_a_chart_nobody_snapshotted(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await uow.commit()

        response = await client.get(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/chart",
            params={"type": "weekly"},
        )
        body = response.json()

        assert response.status_code == 200
        assert body["data"]["points"] == []

    async def test_a_window_nobody_charts_is_refused(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await uow.commit()

        response = await client.get(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/chart",
            params={"type": "hourly"},
        )

        assert response.status_code == 422


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheSourceChartRoutes:
    async def test_a_line_is_served_once_per_source(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        now = _now()
        await SourcePriceTickerRepository(uow).bulk_create(
            [
                SourcePriceTickerModel(
                    symbol_id=symbol.id,
                    source_id=source.id,
                    price=100,
                    timestamp=now,
                )
            ]
        )
        await uow.commit()

        response = await client.get(
            f"/symbols/{SYMBOL_ID_ENCRYPTION.encode(symbol.id)}/chart",
            params={"type": "daily"},
        )
        body = response.json()

        assert response.status_code == 200
        assert body["data"]["source_points"]["tgju"][0]["price"] == 100
        assert body["meta"]["sources"][0]["code"] == "tgju"
        assert body["meta"]["symbols"][0]["code"] == "gold18_gram"
        assert body["meta"]["sources"][0]["id"] == SOURCE_ID_ENCRYPTION.encode(
            source.id
        )
        assert body["meta"]["symbols"][0]["id"] == SYMBOL_ID_ENCRYPTION.encode(
            symbol.id
        )

    async def test_one_source_on_one_line_is_served_with_its_move(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        now = _now()
        await SourcePriceTickerRepository(uow).bulk_create(
            [
                SourcePriceTickerModel(
                    symbol_id=symbol.id,
                    source_id=source.id,
                    price=price,
                    timestamp=now - stamp * _minute,
                )
                for stamp, price in [(10, 200), (5, 150)]
            ]
        )
        await uow.commit()

        response = await client.get(
            f"/sources/{SOURCE_ID_ENCRYPTION.encode(source.id)}"
            f"/symbols/{SYMBOL_ID_ENCRYPTION.encode(symbol.id)}/chart",
            params={"type": "daily"},
        )
        body = response.json()

        assert response.status_code == 200
        assert [p["price"] for p in body["data"]["points"]] == [200, 150]
        assert body["data"]["change_rate"] == pytest.approx(-0.25)

    async def test_a_line_that_source_never_quoted(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        await uow.commit()

        response = await client.get(
            f"/sources/{SOURCE_ID_ENCRYPTION.encode(source.id)}"
            f"/symbols/{SYMBOL_ID_ENCRYPTION.encode(symbol.id)}/chart",
            params={"type": "monthly"},
        )
        body = response.json()

        assert response.status_code == 200
        assert body["data"]["points"] == []
        assert body["meta"]["sources"] == []
