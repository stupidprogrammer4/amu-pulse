import pytest

from src.common.utils import date_utils
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.models import PriceTickerModel
from src.modules.chart.ticker.infra.repository import PriceTickerRepository
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from tests.conftest import NullScheduler

_minute = 60
_hour = 60 * 60
_day = 24 * _hour


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(
        AssetCreate(title="طلا", code=code, primary_color="#c8a44b")
    )
    return asset


async def _points(
    uow: PGUnitOfWork,
    asset: AssetModel,
    stamps: list[int],
) -> None:
    repo = PriceTickerRepository(uow)
    await repo.bulk_create(
        [
            PriceTickerModel(asset_id=asset.id, price=stamp, timestamp=stamp)
            for stamp in stamps
        ]
    )


def _now() -> int:
    return int(date_utils.utc_now().timestamp())


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheDailyChart:
    async def test_every_five_minute_point_is_kept(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        stamps = [now - step * 5 * _minute for step in range(6)]
        await _points(uow, asset, stamps)

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.DAILY, now
        )

        assert [row.timestamp for row in found] == sorted(stamps)

    async def test_the_points_come_back_oldest_first(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await _points(uow, asset, [now - 10 * _minute, now, now - 5 * _minute])

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.DAILY, now
        )

        stamps = [row.timestamp for row in found]
        assert stamps == sorted(stamps)

    async def test_yesterday_is_out_of_the_window(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await _points(uow, asset, [now - _day - _hour, now])

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.DAILY, now
        )

        assert [row.timestamp for row in found] == [now]

    async def test_another_asset_is_never_charted(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        now = _now()
        await _points(uow, gold, [now])
        await _points(uow, dollar, [now])

        found = await PriceTickerRepository(uow).get_chart(
            gold.id, ChartType.DAILY, now
        )

        assert [row.asset_id for row in found] == [gold.id]

    async def test_an_asset_nobody_snapshotted(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.DAILY, _now()
        )

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheCoarserCharts:
    async def test_the_weekly_chart_keeps_one_point_a_half_hour(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        base = (now // (30 * _minute)) * 30 * _minute
        stamps = [base + step * 5 * _minute for step in range(6)]
        await _points(uow, asset, stamps)

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.WEEKLY, now
        )

        assert [row.timestamp for row in found] == [max(stamps)]

    async def test_two_half_hours_are_two_points(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        base = (now // (30 * _minute)) * 30 * _minute
        stamps = [base - 30 * _minute, base - 25 * _minute, base]
        await _points(uow, asset, stamps)

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.WEEKLY, now
        )

        assert [row.timestamp for row in found] == [
            base - 25 * _minute,
            base,
        ]

    async def test_the_monthly_chart_keeps_one_point_two_hours(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        base = (now // (2 * _hour)) * 2 * _hour
        stamps = [base, base + _hour]
        await _points(uow, asset, stamps)

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.MONTHLY, now
        )

        assert [row.timestamp for row in found] == [max(stamps)]

    async def test_the_six_monthly_chart_reaches_back_half_a_year(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        stamps = [now - 100 * _day, now]
        await _points(uow, asset, stamps)

        monthly = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.MONTHLY, now
        )
        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.SIX_MONTHLY, now
        )

        assert [row.timestamp for row in monthly] == [now]
        assert [row.timestamp for row in found] == stamps

    async def test_the_yearly_chart_keeps_one_point_a_day(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        base = (now // _day) * _day
        stamps = [base, base + _hour, base - _day]
        await _points(uow, asset, stamps)

        found = await PriceTickerRepository(uow).get_chart(
            asset.id, ChartType.YEARLY, now
        )

        assert [row.timestamp for row in found] == [
            base - _day,
            base + _hour,
        ]
