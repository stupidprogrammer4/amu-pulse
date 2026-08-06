import src.tasks.broker  # noqa: F401
from src.modules.price.calculator.tasks.price import (
    calculate_asset,
    calculate_usd,
)


class TestTheDollarSchedule:
    def test_the_dollar_is_priced_every_twenty_seconds(self) -> None:
        assert calculate_usd.labels["schedule"] == [{"interval": 20}]

    def test_nothing_but_the_task_itself_decides_that_period(self) -> None:
        assert calculate_usd.task_name == "calculator.calculate_usd"
        assert calculate_usd.labels["queue_name"] == "calculator_queue"

    def test_every_other_asset_is_scheduled_from_its_config(self) -> None:
        assert "schedule" not in calculate_asset.labels
