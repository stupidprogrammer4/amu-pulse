import pytest
from httpx import AsyncClient

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
    AssetSwitchService,
)
from src.modules.price.assets.config.constants import (
    ASSET_ID_ENCRYPTION,
    ASSET_SWITCH_ID_ENCRYPTION,
)
from src.modules.price.assets.domain.dtos import (
    AssetCreate,
    AssetSwitchCreate,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import (
    AssetModel,
    AssetSwitchModel,
)
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from tests.conftest import NullScheduler


async def _asset(uow: PGUnitOfWork) -> AssetModel:
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


async def _switch(
    uow: PGUnitOfWork,
    asset: AssetModel,
    switch: SourceSwitch = SourceSwitch.IRAN_MARKET,
) -> AssetSwitchModel:
    switches = AssetSwitchService(AssetSwitchRepository(uow))
    row = await switches.create(
        asset.id, AssetSwitchCreate(switch=switch, priority=0)
    )
    return row


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheAssetIsReadOffThePathAlone:
    async def test_the_order_is_served_without_a_query_string(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await _switch(uow, asset)
        await uow.commit()

        response = await client.get(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/switches"
        )
        body = response.json()

        assert response.status_code == 200
        assert body["data"][0]["switch"] == "iran_market"

    async def test_a_market_is_added_off_the_path_alone(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await uow.commit()

        response = await client.post(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/switches",
            json={"switch": "supplier", "priority": 0},
        )

        assert response.status_code == 200
        assert response.json()["data"]["switch"] == "supplier"

    async def test_a_row_is_patched_off_the_path_alone(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        row = await _switch(uow, asset)
        await uow.commit()

        response = await client.patch(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/switches"
            f"/{ASSET_SWITCH_ID_ENCRYPTION.encode(row.id)}",
            json={"priority": 3},
        )

        assert response.status_code == 200
        assert response.json()["data"]["priority"] == 3

    async def test_a_row_is_dropped_off_the_path_alone(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        row = await _switch(uow, asset)
        await uow.commit()

        response = await client.delete(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/switches"
            f"/{ASSET_SWITCH_ID_ENCRYPTION.encode(row.id)}"
        )

        assert response.status_code == 200

    async def test_a_batch_is_written_off_the_path_alone(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await uow.commit()

        response = await client.post(
            f"/assets/{ASSET_ID_ENCRYPTION.encode(asset.id)}/switches/batch",
            json={
                "items": [
                    {"switch": "iran_market", "priority": 0},
                    {"switch": "supplier", "priority": 1},
                ]
            },
        )

        assert response.status_code == 200
        assert len(response.json()["data"]) == 2

    async def test_an_id_no_asset_carries_is_a_not_found(
        self, client: AsyncClient, uow: PGUnitOfWork
    ) -> None:
        response = await client.get("/assets/404404404/switches")

        assert response.status_code == 404
