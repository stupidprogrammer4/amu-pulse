from collections.abc import AsyncIterator

import pytest
from redis.exceptions import RedisError
from taskiq_redis import RedisScheduleSource

from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import AssetConfigUpdate, AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.calculator.app.services import SchedulerService
from src.modules.price.calculator.infra.readers import AssetReader


@pytest.fixture
async def schedules(
    integration_settings: Settings,
) -> AsyncIterator[RedisScheduleSource]:
    # never touch the prefix a running scheduler is reading
    source = RedisScheduleSource(
        url=integration_settings.taskiq.redis_url,
        prefix="test:calc:schedule",
        max_connection_pool_size=2,
    )
    try:
        await source.get_schedules()
    except (RedisError, OSError) as exc:
        await source.shutdown()
        pytest.skip(f"redis is not reachable: {exc}")
    try:
        yield source
    finally:
        for schedule in await source.get_schedules():
            await source.delete_schedule(schedule.schedule_id)
        await source.shutdown()


def _assets(uow: PGUnitOfWork) -> tuple[AssetService, AssetConfigService]:
    """
    Desc: Build the asset services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (tuple[AssetService, AssetConfigService]): The two services.
    """
    configs = AssetConfigService(AssetConfigRepository(uow))
    return AssetService(AssetRepository(uow), configs), configs


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset with its default, paused config.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
    assets, _ = _assets(uow)
    asset = await assets.create(AssetCreate(title="طلا", code=code))
    return asset


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSchedulerServiceAgainstRealInfra:
    async def test_switching_it_on_schedules_the_asset(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow)
        _, configs = _assets(uow)
        await configs.update(
            asset.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=45),
        )
        service = SchedulerService(AssetReader(uow), schedules)

        scheduled = await service.sync(asset.id)
        found = await schedules.get_schedules()

        assert scheduled is True
        assert len(found) == 1
        assert found[0].schedule_id == f"calculator:asset:{asset.id}"
        assert found[0].task_name == "calculator.calculate_asset"
        assert found[0].interval == 45
        assert found[0].kwargs == {"asset_id": asset.id}

    async def test_a_brand_new_asset_is_never_scheduled(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        # creating an asset must not start pricing it on its own
        asset = await _asset(uow)
        service = SchedulerService(AssetReader(uow), schedules)

        scheduled = await service.sync(asset.id)
        found = await schedules.get_schedules()

        assert scheduled is False
        assert list(found) == []

    async def test_switching_it_off_takes_the_schedule_away(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow)
        _, configs = _assets(uow)
        service = SchedulerService(AssetReader(uow), schedules)
        await configs.update(asset.id, AssetConfigUpdate(scheduler_on=True))
        await service.sync(asset.id)

        await configs.update(asset.id, AssetConfigUpdate(scheduler_on=False))
        scheduled = await service.sync(asset.id)
        found = await schedules.get_schedules()

        assert scheduled is False
        assert list(found) == []

    async def test_a_new_period_replaces_the_old_schedule(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow)
        _, configs = _assets(uow)
        service = SchedulerService(AssetReader(uow), schedules)
        await configs.update(
            asset.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=60),
        )
        await service.sync(asset.id)

        await configs.update(asset.id, AssetConfigUpdate(scheduler_seconds=20))
        await service.sync(asset.id)
        found = await schedules.get_schedules()

        assert len(found) == 1
        assert found[0].interval == 20

    async def test_an_asset_that_is_gone_is_unscheduled(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow)
        assets, configs = _assets(uow)
        service = SchedulerService(AssetReader(uow), schedules)
        await configs.update(asset.id, AssetConfigUpdate(scheduler_on=True))
        await service.sync(asset.id)

        await assets.remove(asset.id)
        scheduled = await service.sync(asset.id)
        found = await schedules.get_schedules()

        assert scheduled is False
        assert list(found) == []

    async def test_each_asset_keeps_its_own_period(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        _, configs = _assets(uow)
        service = SchedulerService(AssetReader(uow), schedules)
        await configs.update(
            gold.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=30),
        )
        await configs.update(
            dollar.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=20),
        )

        await service.sync(gold.id)
        await service.sync(dollar.id)
        found = await schedules.get_schedules()

        # the dollar keeps its own fixed period, off the config entirely
        assert {row.schedule_id: row.interval for row in found} == {
            f"calculator:asset:{gold.id}": 30,
        }

    async def test_the_dollar_is_never_put_on_a_schedule(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        # it runs on its own fixed period, so no config can schedule it
        dollar = await _asset(uow, AssetCode.USD)
        _, configs = _assets(uow)
        await configs.update(
            dollar.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=300),
        )
        service = SchedulerService(AssetReader(uow), schedules)

        scheduled = await service.sync(dollar.id)
        found = await schedules.get_schedules()

        assert scheduled is False
        assert list(found) == []
