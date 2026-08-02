import pytest

from src.common.errors.exceptions import NotFoundException, ValidationException
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetUpdate,
)
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from tests.conftest import NullScheduler


def _services(uow: PGUnitOfWork) -> tuple[AssetService, AssetConfigService]:
    """
    Desc: Build the asset and asset-config services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to read and write through.
    Returns:
        return (tuple[AssetService, AssetConfigService]): The two services.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    return assets, configs


def _create_data(code: AssetCode = AssetCode.GOLD18) -> AssetCreate:
    """
    Desc: Build an AssetCreate DTO for the given code.
    Args:
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetCreate): The create DTO.
    """
    return AssetCreate(
        title="طلای ۱۸ عیار",
        code=code,
        primary_color="#c8a44b",
        description="مظنه آب‌شده",
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestAssetServiceCRUD:
    async def test_create_returns_persisted_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)

        asset = await assets.create(_create_data())

        assert asset.id is not None
        assert asset.title == "طلای ۱۸ عیار"
        assert asset.code == AssetCode.GOLD18
        assert asset.description == "مظنه آب‌شده"
        assert asset.created_at is not None

    async def test_create_also_creates_the_default_config(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)

        asset = await assets.create(_create_data())

        config = await configs.get_by_asset_id(asset.id)
        assert config.asset_id == asset.id
        # a new asset is paused until an admin turns it on
        assert config.scheduler_on is False
        assert config.scheduler_seconds == 60
        assert config.agg_type == AggregationType.MEDIAN

    async def test_get_by_id_returns_asset(self, uow: PGUnitOfWork) -> None:
        assets, _ = _services(uow)
        created = await assets.create(_create_data())

        fetched = await assets.get_by_id(created.id)

        assert fetched.id == created.id
        assert fetched.code == AssetCode.GOLD18

    async def test_get_by_id_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await assets.get_by_id(9999)

    async def test_get_all_returns_every_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)
        await assets.create(_create_data(AssetCode.GOLD18))
        await assets.create(_create_data(AssetCode.USD))

        found = await assets.get_all()

        assert {a.code for a in found} == {AssetCode.GOLD18, AssetCode.USD}

    async def test_update_patches_only_set_fields(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)
        created = await assets.create(_create_data())

        updated = await assets.update(
            created.id, AssetUpdate(title="طلای ۲۴ عیار")
        )

        assert updated.title == "طلای ۲۴ عیار"
        assert updated.description == "مظنه آب‌شده"
        assert updated.code == AssetCode.GOLD18

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)
        created = await assets.create(_create_data())

        with pytest.raises(ValidationException):
            await assets.update(created.id, AssetUpdate())

    async def test_update_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await assets.update(9999, AssetUpdate(title="ناموجود"))

    async def test_remove_deletes_asset(self, uow: PGUnitOfWork) -> None:
        assets, _ = _services(uow)
        created = await assets.create(_create_data())

        removed = await assets.remove(created.id)

        assert removed.id == created.id
        with pytest.raises(NotFoundException):
            await assets.get_by_id(created.id)

    async def test_remove_cascades_to_the_config(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)
        created = await assets.create(_create_data())

        await assets.remove(created.id)

        with pytest.raises(NotFoundException):
            await configs.get_by_asset_id(created.id)

    async def test_remove_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await assets.remove(9999)


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestAssetWithConfig:
    async def test_get_all_with_config_eager_loads_the_config(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)
        await assets.create(_create_data(AssetCode.GOLD18))
        await assets.create(_create_data(AssetCode.USD))

        found = await assets.get_all_with_config()

        assert len(found) == 2
        # reached without a second query: joinedload already filled it in
        for asset in found:
            assert asset.config is not None
            assert asset.config.asset_id == asset.id

    async def test_get_all_with_config_is_ordered_by_id(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)
        first = await assets.create(_create_data(AssetCode.GOLD18))
        second = await assets.create(_create_data(AssetCode.USD))

        found = await assets.get_all_with_config()

        assert [a.id for a in found] == [first.id, second.id]

    async def test_get_all_with_config_on_an_empty_table(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _services(uow)

        found = await assets.get_all_with_config()

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestAssetConfigService:
    async def test_update_patches_only_set_fields(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)
        asset = await assets.create(_create_data())

        updated = await configs.update(
            asset.id, AssetConfigUpdate(scheduler_seconds=120)
        )

        assert updated.scheduler_seconds == 120
        assert updated.scheduler_on is False
        assert updated.agg_type == AggregationType.MEDIAN

    async def test_update_writes_every_field(self, uow: PGUnitOfWork) -> None:
        assets, configs = _services(uow)
        asset = await assets.create(_create_data())

        updated = await configs.update(
            asset.id,
            AssetConfigUpdate(
                scheduler_on=False,
                scheduler_seconds=300,
                agg_type=AggregationType.THIRD_QUARTILE,
            ),
        )

        assert updated.scheduler_on is False
        assert updated.scheduler_seconds == 300
        assert updated.agg_type == AggregationType.THIRD_QUARTILE

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)
        asset = await assets.create(_create_data())

        with pytest.raises(ValidationException):
            await configs.update(asset.id, AssetConfigUpdate())

    async def test_update_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        _, configs = _services(uow)

        with pytest.raises(NotFoundException):
            await configs.update(
                9999, AssetConfigUpdate(scheduler_seconds=120)
            )

    async def test_get_by_asset_id_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        _, configs = _services(uow)

        with pytest.raises(NotFoundException):
            await configs.get_by_asset_id(9999)

    async def test_get_all_returns_one_config_per_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)
        first = await assets.create(_create_data(AssetCode.GOLD18))
        second = await assets.create(_create_data(AssetCode.USD))

        found = await configs.get_all()

        assert {c.asset_id for c in found} == {first.id, second.id}


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheDollarDefaults:
    async def test_the_dollar_starts_on_its_own_period(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)
        dollar = await assets.create(
            AssetCreate(
                title="دلار", code=AssetCode.USD, primary_color="#c8a44b"
            )
        )

        config = await configs.get_by_asset_id(dollar.id)

        assert config.scheduler_on is True
        assert config.scheduler_seconds == 20

    async def test_every_other_asset_starts_paused(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, configs = _services(uow)
        gold = await assets.create(_create_data())

        config = await configs.get_by_asset_id(gold.id)

        assert config.scheduler_on is False
        assert config.scheduler_seconds == 60
