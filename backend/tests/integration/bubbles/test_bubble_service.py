import pytest

from src.common.errors.exceptions import NotFoundException, ValidationException
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.bubbles.app.services import (
    BubbleConfigService,
    BubbleService,
)
from src.modules.price.bubbles.domain.dtos import (
    BubbleConfigUpdate,
    BubbleCreate,
    BubbleUpdate,
)
from src.modules.price.bubbles.infra.repository import (
    BubbleConfigRepository,
    BubbleRepository,
)
from src.seeders.bubbles import BUBBLES, seed_bubbles


def _services(
    uow: PGUnitOfWork,
) -> tuple[BubbleService, BubbleConfigService]:
    """
    Desc: Build the bubble and bubble-config services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to read and write through.
    Returns:
        return (tuple[BubbleService, BubbleConfigService]): The two services.
    """
    configs = BubbleConfigService(BubbleConfigRepository(uow))
    bubbles = BubbleService(BubbleRepository(uow), configs)
    return bubbles, configs


def _create_data(code: AssetCode = AssetCode.GOLD18) -> BubbleCreate:
    """
    Desc: Build a BubbleCreate DTO for the given asset code.
    Args:
        code (AssetCode): Asset whose premium the bubble tracks.
    Returns:
        return (BubbleCreate): The create DTO.
    """
    return BubbleCreate(
        title="حباب طلای ۱۸ عیار",
        code=code,
        description="اختلاف قیمت بازار با ارزش ذاتی",
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBubbleServiceCRUD:
    async def test_create_returns_persisted_bubble(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _services(uow)

        bubble = await bubbles.create(_create_data())

        assert bubble.id is not None
        assert bubble.code == AssetCode.GOLD18
        assert bubble.title == "حباب طلای ۱۸ عیار"

    async def test_create_also_creates_the_default_config(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, configs = _services(uow)

        bubble = await bubbles.create(_create_data())

        config = await configs.get_by_bubble_id(bubble.id)
        assert config.bubble_id == bubble.id
        # a new bubble is paused until an admin turns it on
        assert config.scheduler_on is False
        assert config.scheduler_seconds == 60
        assert config.agg_type == AggregationType.MEDIAN

    async def test_get_by_id_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await bubbles.get_by_id(9999)

    async def test_get_all_returns_every_bubble(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _services(uow)
        await bubbles.create(_create_data(AssetCode.GOLD18))
        await bubbles.create(_create_data(AssetCode.USD))

        found = await bubbles.get_all()

        assert {b.code for b in found} == {AssetCode.GOLD18, AssetCode.USD}

    async def test_update_patches_only_set_fields(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _services(uow)
        created = await bubbles.create(_create_data())

        updated = await bubbles.update(
            created.id, BubbleUpdate(title="حباب آب‌شده")
        )

        assert updated.title == "حباب آب‌شده"
        assert updated.code == AssetCode.GOLD18
        assert updated.description == "اختلاف قیمت بازار با ارزش ذاتی"

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _services(uow)
        created = await bubbles.create(_create_data())

        with pytest.raises(ValidationException):
            await bubbles.update(created.id, BubbleUpdate())

    async def test_remove_cascades_to_the_config(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, configs = _services(uow)
        created = await bubbles.create(_create_data())

        await bubbles.remove(created.id)

        with pytest.raises(NotFoundException):
            await configs.get_by_bubble_id(created.id)

    async def test_get_all_with_config_eager_loads_the_config(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _services(uow)
        await bubbles.create(_create_data(AssetCode.GOLD18))
        await bubbles.create(_create_data(AssetCode.USD))

        found = await bubbles.get_all_with_config()

        assert len(found) == 2
        for bubble in found:
            assert bubble.config is not None
            assert bubble.config.bubble_id == bubble.id


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBubbleConfigService:
    async def test_the_aggregation_is_what_folds_many_publishers(
        self, uow: PGUnitOfWork
    ) -> None:
        # a second bubble source needs no schema change, only this setting
        bubbles, configs = _services(uow)
        bubble = await bubbles.create(_create_data())

        updated = await configs.update(
            bubble.id, BubbleConfigUpdate(agg_type=AggregationType.MEAN)
        )

        assert updated.agg_type == AggregationType.MEAN
        assert updated.scheduler_seconds == 60

    async def test_update_patches_only_set_fields(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, configs = _services(uow)
        bubble = await bubbles.create(_create_data())

        updated = await configs.update(
            bubble.id, BubbleConfigUpdate(scheduler_on=True)
        )

        assert updated.scheduler_on is True
        assert updated.agg_type == AggregationType.MEDIAN

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, configs = _services(uow)
        bubble = await bubbles.create(_create_data())

        with pytest.raises(ValidationException):
            await configs.update(bubble.id, BubbleConfigUpdate())

    async def test_update_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        _, configs = _services(uow)

        with pytest.raises(NotFoundException):
            await configs.update(9999, BubbleConfigUpdate(scheduler_on=False))


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBubbleSeeder:
    async def test_it_creates_every_declared_bubble(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_bubbles(uow)

        assert len(created) == len(BUBBLES)
        assert {b.code for b in created} == {s.code for s in BUBBLES}

    async def test_every_seeded_bubble_gets_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_bubbles(uow)
        configs = BubbleConfigService(BubbleConfigRepository(uow))

        for bubble in created:
            config = await configs.get_by_bubble_id(bubble.id)
            assert config.bubble_id == bubble.id

    async def test_running_it_twice_creates_nothing_new(
        self, uow: PGUnitOfWork
    ) -> None:
        await seed_bubbles(uow)

        second = await seed_bubbles(uow)

        assert second == []
