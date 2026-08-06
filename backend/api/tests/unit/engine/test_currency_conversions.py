from decimal import Decimal

import pytest

from src.common.constants import MAZANE_FACTOR
from src.common.utils import currency_utils


class TestMazane:
    def test_a_mazane_converts_to_its_per_gram_price(self) -> None:
        assert currency_utils.from_mazane(4_331_802) == 1_000_000

    def test_a_per_gram_price_converts_to_its_mazane(self) -> None:
        assert currency_utils.to_mazane(1_000_000) == 4_331_800

    @pytest.mark.parametrize("per_gram", [1_000, 185_820_000, 197_631_000])
    def test_the_round_trip_holds_within_a_ten(self, per_gram: int) -> None:
        back = currency_utils.from_mazane(currency_utils.to_mazane(per_gram))

        assert abs(back - per_gram) <= 10

    def test_a_mazane_is_worth_more_than_a_gram(self) -> None:
        assert currency_utils.to_mazane(1_000_000) > 1_000_000
        assert currency_utils.from_mazane(1_000_000) < 1_000_000

    def test_the_factor_is_the_published_one(self) -> None:
        assert MAZANE_FACTOR == Decimal("4.331802")


class TestDollarAndBubble:
    def test_a_dollar_amount_converts_to_rial(self) -> None:
        rial = currency_utils.from_usd(Decimal("100"), 1_931_900)

        assert rial == 193_190_000

    def test_a_fractional_amount_lands_on_a_ten(self) -> None:
        rial = currency_utils.from_usd(Decimal("96.452240"), 1_931_900)

        assert rial == 186_336_080

    def test_a_positive_bubble_lifts_the_price(self) -> None:
        assert currency_utils.with_bubble(190_000_000, 3_241_000) == (
            193_241_000
        )

    def test_a_negative_bubble_lowers_it(self) -> None:
        assert currency_utils.with_bubble(190_000_000, -2_137_540) == (
            187_862_460
        )

    def test_a_zero_bubble_leaves_the_price_alone(self) -> None:
        assert currency_utils.with_bubble(190_000_000, 0) == 190_000_000


class TestRoundRial:
    def test_a_price_always_ends_in_a_zero(self) -> None:
        assert currency_utils.round_rial(197_631_004) == 197_631_000

    def test_it_rounds_to_the_nearest_ten(self) -> None:
        assert currency_utils.round_rial(195) == 200
        assert currency_utils.round_rial(194) == 190

    def test_it_takes_a_decimal(self) -> None:
        assert currency_utils.round_rial(Decimal("1934.5")) == 1930

    def test_it_leaves_a_round_price_alone(self) -> None:
        assert currency_utils.round_rial(1_931_900) == 1_931_900

    def test_a_negative_amount_still_lands_on_a_ten(self) -> None:
        assert currency_utils.round_rial(-2_137_544) == -2_137_540
