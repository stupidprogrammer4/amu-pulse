from collections.abc import AsyncIterator

import pytest
from redis.exceptions import RedisError
from taskiq_redis import RedisScheduleSource

from src.common.errors.exceptions import ValidationException
from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import AssetConfigUpdate, AssetCreate
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.calculator.app.services import SchedulerService


@pytest.fixture
async def schedules(
    integration_settings: Settings,
) -> AsyncIterator[RedisScheduleSource]:
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


def _assets(
    uow: PGUnitOfWork,
    schedules: RedisScheduleSource,
) -> tuple[AssetService, AssetConfigService]:
    configs = AssetConfigService(
        AssetConfigRepository(uow),
        AssetRepository(uow),
        SchedulerService(schedules),
    )
    return AssetService(AssetRepository(uow), configs), configs


async def _asset(
    uow: PGUnitOfWork,
    schedules: RedisScheduleSource,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    assets, _ = _assets(uow, schedules)
    asset = await assets.create(
        AssetCreate(title="طلا", code=code, primary_color="#c8a44b")
    )
    return asset


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestConfigWritesTheSchedule:
    async def test_switching_it_on_schedules_the_asset(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow, schedules)
        _, configs = _assets(uow, schedules)

        await configs.update(
            asset.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=45),
        )
        found = await schedules.get_schedules()

        assert len(found) == 1
        assert found[0].schedule_id == f"calculator:asset:{asset.id}"
        assert found[0].task_name == "calculator.calculate_asset"
        assert found[0].interval == 45
        assert found[0].kwargs == {"asset_id": asset.id}

    async def test_a_brand_new_asset_is_never_scheduled(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        await _asset(uow, schedules)

        found = await schedules.get_schedules()

        assert list(found) == []

    async def test_switching_it_off_takes_the_schedule_away(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow, schedules)
        _, configs = _assets(uow, schedules)
        await configs.update(asset.id, AssetConfigUpdate(scheduler_on=True))

        await configs.update(asset.id, AssetConfigUpdate(scheduler_on=False))
        found = await schedules.get_schedules()

        assert list(found) == []

    async def test_a_new_period_replaces_the_old_schedule(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow, schedules)
        _, configs = _assets(uow, schedules)
        await configs.update(
            asset.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=60),
        )

        await configs.update(asset.id, AssetConfigUpdate(scheduler_seconds=20))
        found = await schedules.get_schedules()

        assert len(found) == 1
        assert found[0].interval == 20

    async def test_a_period_written_while_paused_schedules_nothing(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow, schedules)
        _, configs = _assets(uow, schedules)

        await configs.update(asset.id, AssetConfigUpdate(scheduler_seconds=25))
        found = await schedules.get_schedules()

        assert list(found) == []

    async def test_a_rule_change_leaves_the_schedule_alone(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        asset = await _asset(uow, schedules)
        _, configs = _assets(uow, schedules)
        await configs.update(
            asset.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=45),
        )

        await configs.update(
            asset.id,
            AssetConfigUpdate(agg_type=AggregationType.MEAN),
        )
        found = await schedules.get_schedules()

        assert len(found) == 1
        assert found[0].interval == 45

    async def test_the_dollar_config_is_refused(
        self, uow: PGUnitOfWork, schedules: RedisScheduleSource
    ) -> None:
        gold = await _asset(uow, schedules)
        dollar = await _asset(uow, schedules, AssetCode.USD)
        _, configs = _assets(uow, schedules)
        await configs.update(
            gold.id,
            AssetConfigUpdate(scheduler_on=True, scheduler_seconds=30),
        )

        with pytest.raises(ValidationException):
            await configs.update(
                dollar.id,
                AssetConfigUpdate(scheduler_on=True, scheduler_seconds=20),
            )
        found = await schedules.get_schedules()

        assert {row.schedule_id: row.interval for row in found} == {
            f"calculator:asset:{gold.id}": 30,
        }
