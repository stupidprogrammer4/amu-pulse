from typing import Sequence, cast

from taskiq import ScheduledTask, ScheduleSource

from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.domain.models import AssetConfigModel
from src.modules.price.calculator.app.services import SchedulerService
from src.modules.price.calculator.domain.context import AssetContext
from src.modules.price.calculator.infra.readers import AssetReader


class _FakeScheduleSource:
    """The two writes the service makes, over a dict of schedules."""

    def __init__(self) -> None:
        self.schedules: dict[str, ScheduledTask] = {}
        self.deleted: list[str] = []

    async def add_schedule(self, schedule: ScheduledTask) -> None:
        self.schedules[schedule.schedule_id] = schedule

    async def delete_schedule(self, schedule_id: str) -> None:
        self.deleted.append(schedule_id)
        self.schedules.pop(schedule_id, None)

    async def get_schedules(self) -> Sequence[ScheduledTask]:
        return list(self.schedules.values())


class _FakeAssetReader:
    """The one asset read the service makes."""

    def __init__(self, assets: Sequence[AssetContext]) -> None:
        self.assets = assets

    async def get_asset_config(self, asset_id: int) -> AssetContext | None:
        found = None
        for asset in self.assets:
            if asset.asset_id == asset_id:
                found = asset
        return found


def _asset(
    asset_id: int = 1,
    code: AssetCode = AssetCode.GOLD18,
    scheduler_on: bool = True,
    seconds: int = 60,
) -> AssetContext:
    """
    Desc: Build an asset context with the scheduler config given.
    Args:
        asset_id (int): ID of the asset.
        code (AssetCode): Code of the asset.
        scheduler_on (bool): Whether its scheduler is switched on.
        seconds (int): How often it should be priced.
    Returns:
        return (AssetContext): The context the service reads.
    """
    config = AssetConfigModel(
        asset_id=asset_id,
        scheduler_on=scheduler_on,
        scheduler_seconds=seconds,
        agg_type=AggregationType.MEDIAN,
    )
    return AssetContext(code=code, asset_id=asset_id, config=config)


def _service(
    assets: Sequence[AssetContext],
    source: _FakeScheduleSource | None = None,
) -> tuple[SchedulerService, _FakeScheduleSource]:
    """
    Desc: Build the service over a fake reader and a fake schedule source.
    Args:
        assets (Sequence[AssetContext]): The assets that exist.
        source (_FakeScheduleSource | None): The schedules already written,
            a fresh set when none is given.
    Returns:
        return (tuple[SchedulerService, _FakeScheduleSource]): The service
            and the schedules it writes to.
    """
    written = source or _FakeScheduleSource()
    service = SchedulerService(
        cast(AssetReader, _FakeAssetReader(assets)),
        cast(ScheduleSource, written),
    )
    return service, written


class TestSync:
    async def test_switching_it_on_schedules_the_asset(self) -> None:
        service, source = _service([_asset(seconds=45)])

        scheduled = await service.sync(1)

        assert scheduled is True
        schedule = source.schedules["calculator:asset:1"]
        assert schedule.task_name == "calculator.calculate_asset"
        assert schedule.interval == 45
        assert schedule.kwargs == {"asset_id": 1}

    async def test_the_schedule_fires_on_the_module_queue(self) -> None:
        service, source = _service([_asset()])

        await service.sync(1)

        schedule = source.schedules["calculator:asset:1"]
        assert schedule.labels == {"queue_name": "calculator_queue"}

    async def test_a_switched_off_asset_gets_no_schedule(self) -> None:
        service, source = _service([_asset(scheduler_on=False)])

        scheduled = await service.sync(1)

        assert scheduled is False
        assert source.schedules == {}

    async def test_switching_it_off_takes_the_schedule_away(self) -> None:
        service, source = _service([_asset()])
        await service.sync(1)

        off, _ = _service([_asset(scheduler_on=False)], source)
        scheduled = await off.sync(1)

        assert scheduled is False
        assert source.schedules == {}

    async def test_a_new_period_replaces_the_old_schedule(self) -> None:
        service, source = _service([_asset(seconds=60)])
        await service.sync(1)

        faster, _ = _service([_asset(seconds=20)], source)
        await faster.sync(1)

        assert len(source.schedules) == 1
        assert source.schedules["calculator:asset:1"].interval == 20

    async def test_an_asset_that_is_gone_is_unscheduled(self) -> None:
        service, source = _service([])

        scheduled = await service.sync(9999)

        assert scheduled is False
        assert "calculator:asset:9999" in source.deleted

    async def test_each_asset_keeps_its_own_schedule(self) -> None:
        service, source = _service(
            [
                _asset(asset_id=1, seconds=30),
                _asset(asset_id=2, code=AssetCode.USD, seconds=20),
            ]
        )

        await service.sync(1)
        await service.sync(2)

        assert {
            id: schedule.interval for id, schedule in source.schedules.items()
        } == {"calculator:asset:1": 30, "calculator:asset:2": 20}
