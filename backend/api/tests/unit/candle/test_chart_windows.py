from datetime import UTC, datetime, timedelta

from src.modules.chart.candle.app.helpers import ChartWindow
from src.modules.chart.candle.domain.dtos import ParamDTO
from src.modules.chart.candle.domain.enums import TimeFrame

_to = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def _param(days: float) -> ParamDTO:
    """
    Desc: Build the span a chart is asked for, that many days long.
    Args:
        days (float): How many days it covers.
    Returns:
        return (ParamDTO): The span.
    """
    return ParamDTO(from_datetime=_to - timedelta(days=days), to_datetime=_to)


class TestHowLongASpanIs:
    def test_a_span_is_counted_in_days(self) -> None:
        window = ChartWindow()

        assert window.days(_param(3)) == 3

    def test_half_a_day_is_half_a_day(self) -> None:
        window = ChartWindow()

        assert window.days(_param(0.5)) == 0.5


class TestHowFineTheCandlesAreCut:
    def test_a_span_of_hours_is_drawn_five_minutes_at_a_time(self) -> None:
        window = ChartWindow()

        assert window.timeframe(window.days(_param(0.25))) is (
            TimeFrame.FIVE_MINUTE
        )

    def test_a_day_is_still_drawn_five_minutes_at_a_time(self) -> None:
        window = ChartWindow()

        assert window.timeframe(1) is TimeFrame.FIVE_MINUTE

    def test_a_week_is_drawn_hour_by_hour(self) -> None:
        window = ChartWindow()

        assert window.timeframe(1.5) is TimeFrame.HOURLY
        assert window.timeframe(7) is TimeFrame.HOURLY

    def test_two_months_are_drawn_five_hours_at_a_time(self) -> None:
        window = ChartWindow()

        assert window.timeframe(8) is TimeFrame.FIVE_HOURLY
        assert window.timeframe(60) is TimeFrame.FIVE_HOURLY

    def test_anything_longer_is_drawn_day_by_day(self) -> None:
        window = ChartWindow()

        assert window.timeframe(61) is TimeFrame.DAILY
        assert window.timeframe(365) is TimeFrame.DAILY
