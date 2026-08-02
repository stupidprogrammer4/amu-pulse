from src.modules.chart.ticker.domain.enums import ChartType


class TestTheStep:
    def test_a_day_is_drawn_every_five_minutes(self) -> None:
        assert ChartType.DAILY.step == 5 * 60

    def test_a_week_is_drawn_every_half_hour(self) -> None:
        assert ChartType.WEEKLY.step == 30 * 60

    def test_a_month_is_drawn_every_two_hours(self) -> None:
        assert ChartType.MONTHLY.step == 2 * 60 * 60

    def test_six_months_are_drawn_every_twelve_hours(self) -> None:
        assert ChartType.SIX_MONTHLY.step == 12 * 60 * 60

    def test_a_year_is_drawn_every_day(self) -> None:
        assert ChartType.YEARLY.step == 24 * 60 * 60


class TestTheWindow:
    def test_each_chart_reaches_back_its_own_name(self) -> None:
        day = 24 * 60 * 60
        assert ChartType.DAILY.span == day
        assert ChartType.WEEKLY.span == 7 * day
        assert ChartType.MONTHLY.span == 30 * day
        assert ChartType.SIX_MONTHLY.span == 180 * day
        assert ChartType.YEARLY.span == 365 * day

    def test_no_chart_is_finer_than_the_snapshots(self) -> None:
        # nothing is written more often than every five minutes
        assert all(type.step >= 5 * 60 for type in ChartType)

    def test_every_chart_holds_a_readable_number_of_points(self) -> None:
        # a chart that asked for more would be plotting noise
        assert all(type.span // type.step <= 500 for type in ChartType)
