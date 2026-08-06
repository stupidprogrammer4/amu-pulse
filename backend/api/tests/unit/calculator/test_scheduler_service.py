from typing import Sequence, cast

from taskiq import ScheduledTask, ScheduleSource

from src.modules.price.calculator.app.services import SchedulerService


class _FakeScheduleSource:

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


def _service(
    source: _FakeScheduleSource | None = None,
) -> tuple[SchedulerService, _FakeScheduleSource]:
    written = source or _FakeScheduleSource()
    return SchedulerService(cast(ScheduleSource, written)), written


class TestSync:
    async def test_switching_it_on_schedules_the_asset(self) -> None:
        service, source = _service()

        scheduled = await service.sync(1, True, 45)

        assert scheduled is True
        schedule = source.schedules["calculator:asset:1"]
        assert schedule.task_name == "calculator.calculate_asset"
        assert schedule.interval == 45
        assert schedule.kwargs == {"asset_id": 1}

    async def test_the_schedule_fires_on_the_module_queue(self) -> None:
        service, source = _service()

        await service.sync(1, True, 60)

        schedule = source.schedules["calculator:asset:1"]
        assert schedule.labels == {"queue_name": "calculator_queue"}

    async def test_a_switched_off_asset_gets_no_schedule(self) -> None:
        service, source = _service()

        scheduled = await service.sync(1, False, 60)

        assert scheduled is False
        assert source.schedules == {}

    async def test_switching_it_off_takes_the_schedule_away(self) -> None:
        service, source = _service()
        await service.sync(1, True, 60)

        scheduled = await service.sync(1, False, 60)

        assert scheduled is False
        assert source.schedules == {}

    async def test_a_new_period_replaces_the_old_schedule(self) -> None:
        service, source = _service()
        await service.sync(1, True, 60)

        await service.sync(1, True, 20)

        assert len(source.schedules) == 1
        assert source.schedules["calculator:asset:1"].interval == 20

    async def test_a_paused_asset_is_swept_off_the_source(self) -> None:
        service, source = _service()

        await service.sync(9999, False, 60)

        assert "calculator:asset:9999" in source.deleted

    async def test_each_asset_keeps_its_own_period(self) -> None:
        service, source = _service()

        await service.sync(1, True, 30)
        await service.sync(2, True, 20)

        assert {
            id: schedule.interval for id, schedule in source.schedules.items()
        } == {"calculator:asset:1": 30, "calculator:asset:2": 20}
