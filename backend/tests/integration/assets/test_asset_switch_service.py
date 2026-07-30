import pytest
from sqlalchemy.exc import IntegrityError

from src.common.errors.exceptions import (
    NotFoundException,
    ValidationException,
)
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
    AssetSwitchService,
)
from src.modules.price.assets.config.constants import (
    ASSET_SWITCH_ID_ENCRYPTION,
)
from src.modules.price.assets.domain.dtos import (
    AssetCreate,
    AssetSwitchBatchCreate,
    AssetSwitchBatchDelete,
    AssetSwitchBatchUpdate,
    AssetSwitchCreate,
    AssetSwitchPriorityUpdate,
    AssetSwitchUpdate,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.sources.domain.enums import SourceSwitch


def _services(uow: PGUnitOfWork) -> tuple[AssetService, AssetSwitchService]:
    """
    Desc: Build the asset and asset-switch services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to read and write through.
    Returns:
        return (tuple[AssetService, AssetSwitchService]): The two services.
    """
    configs = AssetConfigService(AssetConfigRepository(uow))
    assets = AssetService(AssetRepository(uow), configs)
    switches = AssetSwitchService(AssetSwitchRepository(uow))
    return assets, switches


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset to hang a pricing order off.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
    assets, _ = _services(uow)
    asset = await assets.create(AssetCreate(title="طلا", code=code))
    return asset


def _order(*items: tuple[SourceSwitch, int]) -> AssetSwitchBatchCreate:
    """
    Desc: Build a pricing order out of market and level pairs.
    Args:
        items (tuple[SourceSwitch, int]): Each market and its level.
    Returns:
        return (AssetSwitchBatchCreate): The order to write.
    """
    order = AssetSwitchBatchCreate(
        items=[
            AssetSwitchCreate(switch=switch, priority=priority)
            for switch, priority in items
        ]
    )
    return order


def _patch(*items: tuple[SourceSwitch, int]) -> AssetSwitchBatchUpdate:
    """
    Desc: Build a batch patch out of market and level pairs.
    Args:
        items (tuple[SourceSwitch, int]): Each market and its level.
    Returns:
        return (AssetSwitchBatchUpdate): The levels to write.
    """
    patch = AssetSwitchBatchUpdate(
        items=[
            AssetSwitchCreate(switch=switch, priority=priority)
            for switch, priority in items
        ]
    )
    return patch


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBatchCreate:
    async def test_it_stores_every_market_with_its_level(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.GLOBAL_MARKET, 0),
                (SourceSwitch.SUPPLIER, 0),
                (SourceSwitch.IRAN_MARKET, 1),
            ),
        )
        found = await switches.get_by_asset_id(asset.id)

        assert [(row.switch, row.priority) for row in found] == [
            (SourceSwitch.GLOBAL_MARKET, 0),
            (SourceSwitch.SUPPLIER, 0),
            (SourceSwitch.IRAN_MARKET, 1),
        ]

    async def test_two_markets_may_share_a_level(
        self, uow: PGUnitOfWork
    ) -> None:
        # the point of the table: no unique constraint on priority
        _, switches = _services(uow)
        asset = await _asset(uow)

        written = await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.GLOBAL_MARKET, 0),
                (SourceSwitch.SUPPLIER, 0),
            ),
        )

        assert [row.priority for row in written] == [0, 0]

    async def test_a_repeated_market_is_rejected(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.batch_create(
                asset.id,
                _order(
                    (SourceSwitch.SUPPLIER, 0),
                    (SourceSwitch.SUPPLIER, 1),
                ),
            )

    async def test_an_empty_order_is_rejected(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.batch_create(
                asset.id, AssetSwitchBatchCreate(items=[])
            )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSetPriority:
    async def test_it_moves_every_named_market_to_one_level(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.GLOBAL_MARKET, 5),
                (SourceSwitch.SUPPLIER, 7),
                (SourceSwitch.IRAN_MARKET, 9),
            ),
        )

        await switches.set_priority(
            asset.id,
            AssetSwitchPriorityUpdate(
                priority=0,
                switches=[
                    SourceSwitch.GLOBAL_MARKET,
                    SourceSwitch.SUPPLIER,
                ],
            ),
        )
        found = await switches.get_by_asset_id(asset.id)

        assert [(row.switch, row.priority) for row in found] == [
            (SourceSwitch.GLOBAL_MARKET, 0),
            (SourceSwitch.SUPPLIER, 0),
            (SourceSwitch.IRAN_MARKET, 9),
        ]

    async def test_a_market_outside_the_list_keeps_its_level(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.SUPPLIER, 1),
                (SourceSwitch.IRAN_MARKET, 2),
            ),
        )

        await switches.set_priority(
            asset.id,
            AssetSwitchPriorityUpdate(
                priority=0, switches=[SourceSwitch.SUPPLIER]
            ),
        )
        found = await switches.get_by_asset_id(asset.id)

        assert [(row.switch, row.priority) for row in found] == [
            (SourceSwitch.SUPPLIER, 0),
            (SourceSwitch.IRAN_MARKET, 2),
        ]

    async def test_a_market_that_was_never_created_writes_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        # the update joins on existing rows; it never inserts
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id, _order((SourceSwitch.SUPPLIER, 1))
        )

        written = await switches.set_priority(
            asset.id,
            AssetSwitchPriorityUpdate(
                priority=0, switches=[SourceSwitch.GLOBAL_MARKET]
            ),
        )

        assert written == []

    async def test_a_repeated_market_is_rejected(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.set_priority(
                asset.id,
                AssetSwitchPriorityUpdate(
                    priority=0,
                    switches=[
                        SourceSwitch.SUPPLIER,
                        SourceSwitch.SUPPLIER,
                    ],
                ),
            )

    async def test_an_empty_list_is_rejected(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.set_priority(
                asset.id,
                AssetSwitchPriorityUpdate(priority=0, switches=[]),
            )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBatchUpdate:
    async def test_each_market_gets_its_own_level(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.IRAN_MARKET, 0),
                (SourceSwitch.SUPPLIER, 1),
            ),
        )

        await switches.batch_update(
            asset.id,
            _patch(
                (SourceSwitch.IRAN_MARKET, 2),
                (SourceSwitch.SUPPLIER, 0),
            ),
        )
        found = await switches.get_by_asset_id(asset.id)

        assert [(row.switch, row.priority) for row in found] == [
            (SourceSwitch.SUPPLIER, 0),
            (SourceSwitch.IRAN_MARKET, 2),
        ]

    async def test_it_touches_only_the_named_markets(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.GLOBAL_MARKET, 0),
                (SourceSwitch.SUPPLIER, 1),
                (SourceSwitch.IRAN_MARKET, 2),
            ),
        )

        written = await switches.batch_update(
            asset.id, _patch((SourceSwitch.IRAN_MARKET, 0))
        )

        assert [row.switch for row in written] == [SourceSwitch.IRAN_MARKET]
        found = await switches.get_by_asset_id(asset.id)
        assert [(row.switch, row.priority) for row in found] == [
            (SourceSwitch.GLOBAL_MARKET, 0),
            (SourceSwitch.IRAN_MARKET, 0),
            (SourceSwitch.SUPPLIER, 1),
        ]

    async def test_a_repeated_market_is_rejected(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.batch_update(
                asset.id,
                _patch(
                    (SourceSwitch.SUPPLIER, 0),
                    (SourceSwitch.SUPPLIER, 1),
                ),
            )

    async def test_an_empty_order_is_rejected(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.batch_update(
                asset.id, AssetSwitchBatchUpdate(items=[])
            )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestGetByAssetId:
    async def test_an_asset_without_an_order_reads_empty(
        self, uow: PGUnitOfWork
    ) -> None:
        # a new asset is not priced until an admin gives it markets
        _, switches = _services(uow)
        asset = await _asset(uow)

        found = await switches.get_by_asset_id(asset.id)

        assert found == []

    async def test_it_reads_only_its_own_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await switches.batch_create(
            gold.id, _order((SourceSwitch.SUPPLIER, 0))
        )
        await switches.batch_create(
            dollar.id, _order((SourceSwitch.IRAN_MARKET, 0))
        )

        found = await switches.get_by_asset_id(dollar.id)

        assert len(found) == 1
        assert found[0].switch == SourceSwitch.IRAN_MARKET

    async def test_an_update_never_leaks_into_another_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        # the grid joins on switch, so the asset must narrow it
        _, switches = _services(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await switches.batch_create(
            gold.id, _order((SourceSwitch.IRAN_MARKET, 5))
        )
        await switches.batch_create(
            dollar.id, _order((SourceSwitch.IRAN_MARKET, 5))
        )

        await switches.batch_update(
            dollar.id, _patch((SourceSwitch.IRAN_MARKET, 0))
        )
        found = await switches.get_by_asset_id(gold.id)

        assert found[0].priority == 5

    async def test_deleting_the_asset_takes_its_order_with_it(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id, _order((SourceSwitch.SUPPLIER, 0))
        )

        await assets.remove(asset.id)
        found = await switches.get_by_asset_id(asset.id)

        assert found == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestCreate:
    async def test_it_adds_one_market(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        row = await switches.create(
            asset.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=2),
        )

        assert row.id is not None
        assert row.asset_id == asset.id
        assert row.priority == 2

    async def test_the_same_market_twice_is_refused(
        self, uow: PGUnitOfWork
    ) -> None:
        # the unique constraint is what keeps the order unambiguous
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.create(
            asset.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=0),
        )

        with pytest.raises(IntegrityError):
            await switches.create(
                asset.id,
                AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=1),
            )

    async def test_two_assets_may_hold_the_same_market(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)

        await switches.create(
            gold.id,
            AssetSwitchCreate(switch=SourceSwitch.IRAN_MARKET, priority=0),
        )
        row = await switches.create(
            dollar.id,
            AssetSwitchCreate(switch=SourceSwitch.IRAN_MARKET, priority=0),
        )

        assert row.asset_id == dollar.id


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestUpdate:
    async def test_it_patches_one_row(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        row = await switches.create(
            asset.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=5),
        )

        updated = await switches.update(
            asset.id, row.id, AssetSwitchUpdate(priority=0)
        )

        assert updated.id == row.id
        assert updated.priority == 0
        assert updated.switch == SourceSwitch.SUPPLIER

    async def test_it_may_move_the_row_to_another_market(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        row = await switches.create(
            asset.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=1),
        )

        updated = await switches.update(
            asset.id,
            row.id,
            AssetSwitchUpdate(switch=SourceSwitch.GLOBAL_MARKET),
        )

        assert updated.switch == SourceSwitch.GLOBAL_MARKET
        assert updated.priority == 1

    async def test_an_empty_patch_is_rejected(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        row = await switches.create(
            asset.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=1),
        )

        with pytest.raises(ValidationException):
            await switches.update(asset.id, row.id, AssetSwitchUpdate())

    async def test_another_asset_cannot_patch_it(
        self, uow: PGUnitOfWork
    ) -> None:
        # the id alone is not authority; the asset in the path must own it
        _, switches = _services(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        row = await switches.create(
            gold.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=1),
        )

        with pytest.raises(NotFoundException):
            await switches.update(
                dollar.id, row.id, AssetSwitchUpdate(priority=0)
            )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestRemove:
    async def test_it_drops_one_row(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.SUPPLIER, 0),
                (SourceSwitch.IRAN_MARKET, 1),
            ),
        )
        found = await switches.get_by_asset_id(asset.id)

        await switches.remove(asset.id, found[0].id)
        left = await switches.get_by_asset_id(asset.id)

        assert [row.switch for row in left] == [SourceSwitch.IRAN_MARKET]

    async def test_a_missing_row_raises(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(NotFoundException):
            await switches.remove(asset.id, 4040)

    async def test_another_asset_cannot_drop_it(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        row = await switches.create(
            gold.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=0),
        )

        with pytest.raises(NotFoundException):
            await switches.remove(dollar.id, row.id)


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBatchRemove:
    async def test_it_drops_every_named_row(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)
        await switches.batch_create(
            asset.id,
            _order(
                (SourceSwitch.GLOBAL_MARKET, 0),
                (SourceSwitch.SUPPLIER, 1),
                (SourceSwitch.IRAN_MARKET, 2),
            ),
        )
        found = await switches.get_by_asset_id(asset.id)

        dropped = await switches.batch_remove(
            asset.id,
            AssetSwitchBatchDelete(
                ids=[
                    ASSET_SWITCH_ID_ENCRYPTION.encode(found[0].id),
                    ASSET_SWITCH_ID_ENCRYPTION.encode(found[1].id),
                ]
            ),
        )
        left = await switches.get_by_asset_id(asset.id)

        assert len(dropped) == 2
        assert [row.switch for row in left] == [SourceSwitch.IRAN_MARKET]

    async def test_it_drops_nothing_of_another_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        _, switches = _services(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        row = await switches.create(
            gold.id,
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=0),
        )

        dropped = await switches.batch_remove(
            dollar.id,
            AssetSwitchBatchDelete(
                ids=[ASSET_SWITCH_ID_ENCRYPTION.encode(row.id)]
            ),
        )
        left = await switches.get_by_asset_id(gold.id)

        assert dropped == []
        assert len(left) == 1

    async def test_an_empty_list_is_rejected(self, uow: PGUnitOfWork) -> None:
        _, switches = _services(uow)
        asset = await _asset(uow)

        with pytest.raises(ValidationException):
            await switches.batch_remove(
                asset.id, AssetSwitchBatchDelete(ids=[])
            )
