from datetime import datetime, timedelta, timezone

import pytest

from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.domain.models import AssetConfigModel
from src.modules.price.calculator.app.helpers import (
    GlobalMarketCalculator,
    IranMarketCalculator,
    SupplierCalculator,
)
from src.modules.price.calculator.domain.context import AssetContext
from src.modules.price.calculator.domain.results import BubbleResult
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.symbols.domain.enums import CurrencyType

_at = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


def _asset(
    agg: AggregationType = AggregationType.MEDIAN,
    asset_id: int = 1,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetContext:
    """
    Desc: Build an asset context priced by the given rule.
    Args:
        agg (AggregationType): The rule its readings are folded by.
        asset_id (int): ID of the asset.
        code (AssetCode): Code of the asset.
    Returns:
        return (AssetContext): The context a calculator prices.
    """
    config = AssetConfigModel(
        asset_id=asset_id,
        scheduler_on=True,
        scheduler_seconds=60,
        agg_type=agg,
    )
    return AssetContext(code=code, asset_id=asset_id, config=config)


def _reading(
    buying: int,
    selling: int,
    currency: CurrencyType = CurrencyType.RIAL,
    source_id: int = 1,
    priced_at: datetime = _at,
) -> SourcePriceResult:
    """
    Desc: Build one source reading, mid priced like the crawl caches it.
    Args:
        buying (int): The buying side, in the currency's own unit.
        selling (int): The selling side, in the currency's own unit.
        currency (CurrencyType): What the two sides are counted in.
        source_id (int): ID of the source that quoted it.
        priced_at (datetime): When it was quoted.
    Returns:
        return (SourcePriceResult): The reading.
    """
    price = round((buying + selling) / 2)
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=1,
        currency=currency,
        buy_price=buying,
        sell_price=selling,
        price=price,
        buy_spread=price - buying,
        sell_spread=selling - price,
        buy_spread_rate=(price - buying) / price,
        sell_spread_rate=(selling - price) / price,
        priced_at=priced_at,
    )


class TestIranMarketCalculator:
    def test_a_single_reading_is_the_asset_price(self) -> None:
        readings = [_reading(185_000_000, 186_000_000)]

        result = IranMarketCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.asset_id == 1
        assert result.buy_price == 185_000_000
        assert result.sell_price == 186_000_000
        assert result.price == 185_500_000
        assert result.buy_spread == 500_000
        assert result.sell_spread == 500_000

    def test_the_median_is_the_default_rule(self) -> None:
        readings = [
            _reading(100_000_000, 101_000_000),
            _reading(102_000_000, 103_000_000),
            _reading(108_000_000, 109_000_000),
        ]

        result = IranMarketCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.buy_price == 102_000_000
        assert result.sell_price == 103_000_000
        assert result.price == 102_500_000

    @pytest.mark.parametrize(
        ("agg", "buying", "selling"),
        [
            (AggregationType.MEAN, 103_333_330, 104_333_330),
            (AggregationType.MIN, 100_000_000, 101_000_000),
            (AggregationType.MAX, 108_000_000, 109_000_000),
        ],
    )
    def test_each_rule_folds_its_own_way(
        self,
        agg: AggregationType,
        buying: int,
        selling: int,
    ) -> None:
        readings = [
            _reading(100_000_000, 101_000_000),
            _reading(102_000_000, 103_000_000),
            _reading(108_000_000, 109_000_000),
        ]

        result = IranMarketCalculator().calculate(_asset(agg), readings)

        assert result is not None
        assert result.buy_price == buying
        assert result.sell_price == selling

    @pytest.mark.parametrize(
        ("agg", "buying", "selling"),
        [
            (AggregationType.FIRST_QUARTILE, 243_750_000, 244_750_000),
            (AggregationType.THIRD_QUARTILE, 256_250_000, 257_250_000),
        ],
    )
    def test_a_quartile_sits_between_two_readings(
        self,
        agg: AggregationType,
        buying: int,
        selling: int,
    ) -> None:
        readings = [
            _reading(240_000_000, 241_000_000),
            _reading(245_000_000, 246_000_000),
            _reading(255_000_000, 256_000_000),
            _reading(260_000_000, 261_000_000),
        ]

        result = IranMarketCalculator().calculate(_asset(agg), readings)

        assert result is not None
        assert result.buy_price == buying
        assert result.sell_price == selling

    def test_a_source_printing_nonsense_is_dropped(self) -> None:
        readings = [
            _reading(100_000_000, 101_000_000),
            _reading(101_000_000, 102_000_000),
            _reading(150_000_000, 151_000_000),
        ]

        result = IranMarketCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.buy_price == 100_500_000
        assert result.sell_price == 101_500_000

    def test_two_readings_are_never_judged_outliers(self) -> None:
        # with a crowd of two there is no majority to be the odd one out of
        readings = [
            _reading(100_000_000, 101_000_000),
            _reading(150_000_000, 151_000_000),
        ]

        result = IranMarketCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.buy_price == 125_000_000

    def test_a_dollar_reading_is_not_an_iranian_one(self) -> None:
        readings = [_reading(400_000, 401_000, CurrencyType.USD)]

        result = IranMarketCalculator().calculate(_asset(), readings)

        assert result is None

    def test_an_asset_nobody_quoted_has_no_price(self) -> None:
        result = IranMarketCalculator().calculate(_asset(), [])

        assert result is None

    def test_the_price_is_as_fresh_as_its_freshest_reading(self) -> None:
        later = _at + timedelta(minutes=5)
        readings = [
            _reading(100_000_000, 101_000_000),
            _reading(100_000_000, 101_000_000, priced_at=later),
        ]

        result = IranMarketCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.priced_at == later

    def test_the_sweep_skips_the_assets_nobody_quoted(self) -> None:
        gold = _asset(asset_id=1)
        dollar = _asset(asset_id=2, code=AssetCode.USD)
        sources = {1: [_reading(100_000_000, 101_000_000)]}

        results = IranMarketCalculator().calculate_all([gold, dollar], sources)

        assert [r.asset_id for r in results] == [1]

    def test_the_sweep_keeps_the_order_it_was_given(self) -> None:
        assets = [
            _asset(asset_id=2, code=AssetCode.USD),
            _asset(asset_id=1),
        ]
        sources = {
            1: [_reading(100_000_000, 101_000_000)],
            2: [_reading(1_900_000, 1_910_000)],
        }

        results = IranMarketCalculator().calculate_all(assets, sources)

        assert [r.asset_id for r in results] == [2, 1]
        assert results[0].price == 1_905_000


class TestSupplierCalculator:
    def test_a_mazane_is_folded_into_a_per_gram_price(self) -> None:
        # 4_331_802 rial the mazane is exactly 1_000_000 the gram
        readings = [_reading(4_331_802, 4_400_000)]

        result = SupplierCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.buy_price == 1_000_000
        assert result.sell_price == 1_015_740
        assert result.price == 1_007_870

    def test_it_folds_every_supplier_by_the_asset_rule(self) -> None:
        readings = [
            _reading(4_331_802, 4_400_000),
            _reading(4_340_000, 4_410_000),
            _reading(4_350_000, 4_420_000),
        ]

        result = SupplierCalculator().calculate(
            _asset(AggregationType.MIN), readings
        )

        assert result is not None
        assert result.buy_price == 1_000_000

    def test_a_supplier_price_stays_above_zero_spread(self) -> None:
        readings = [_reading(4_331_802, 4_400_000)]

        result = SupplierCalculator().calculate(_asset(), readings)

        assert result is not None
        assert result.sell_price > result.price > result.buy_price

    def test_no_supplier_quoted_the_asset(self) -> None:
        result = SupplierCalculator().calculate(_asset(), [])

        assert result is None


class TestGlobalMarketCalculator:
    def test_an_ounce_of_pure_gold_becomes_a_gram_of_18_carat(self) -> None:
        # $4000.00 the ounce at 1_000_000 rial the dollar
        readings = [_reading(400_000, 400_000, CurrencyType.USD)]

        result = GlobalMarketCalculator().calculate(
            1_000_000, None, _asset(), readings
        )

        assert result is not None
        assert result.price == 96_452_240

    def test_the_premium_lifts_world_parity(self) -> None:
        readings = [_reading(400_000, 400_000, CurrencyType.USD)]
        bubble = BubbleResult(asset_id=1, amount=5_000_000, priced_at=_at)

        result = GlobalMarketCalculator().calculate(
            1_000_000, bubble, _asset(), readings
        )

        assert result is not None
        assert result.price == 101_452_240

    def test_a_market_under_parity_lowers_the_price(self) -> None:
        readings = [_reading(400_000, 400_000, CurrencyType.USD)]
        bubble = BubbleResult(asset_id=1, amount=-2_000_000, priced_at=_at)

        result = GlobalMarketCalculator().calculate(
            1_000_000, bubble, _asset(), readings
        )

        assert result is not None
        assert result.price == 94_452_240

    def test_the_two_sides_survive_the_conversion(self) -> None:
        readings = [_reading(399_000, 401_000, CurrencyType.USD)]

        result = GlobalMarketCalculator().calculate(
            1_000_000, None, _asset(), readings
        )

        assert result is not None
        assert result.buy_price == 96_211_110
        assert result.sell_price == 96_693_370
        assert result.price == 96_452_240

    def test_the_dollar_rate_scales_the_whole_price(self) -> None:
        readings = [_reading(400_000, 400_000, CurrencyType.USD)]

        result = GlobalMarketCalculator().calculate(
            1_931_900, None, _asset(), readings
        )

        assert result is not None
        assert result.price == 186_336_080

    def test_without_a_dollar_rate_nothing_can_be_priced(self) -> None:
        readings = [_reading(400_000, 400_000, CurrencyType.USD)]

        result = GlobalMarketCalculator().calculate(
            0, None, _asset(), readings
        )

        assert result is None

    def test_an_asset_the_world_does_not_price(self) -> None:
        # the dollar itself has no purity of a world-quoted metal
        readings = [_reading(400_000, 400_000, CurrencyType.USD)]
        dollar = _asset(asset_id=2, code=AssetCode.USD)

        result = GlobalMarketCalculator().calculate(
            1_000_000, None, dollar, readings
        )

        assert result is None

    def test_a_rial_reading_is_not_a_world_one(self) -> None:
        readings = [_reading(185_000_000, 186_000_000)]

        result = GlobalMarketCalculator().calculate(
            1_000_000, None, _asset(), readings
        )

        assert result is None

    def test_the_sweep_prices_each_asset_with_its_own_premium(self) -> None:
        gold = _asset(asset_id=1)
        dollar = _asset(asset_id=2, code=AssetCode.USD)
        bubbles = {
            1: BubbleResult(asset_id=1, amount=5_000_000, priced_at=_at)
        }
        sources = {
            1: [_reading(400_000, 400_000, CurrencyType.USD)],
            2: [_reading(400_000, 400_000, CurrencyType.USD)],
        }

        results = GlobalMarketCalculator().calculate_all(
            1_000_000, bubbles, [gold, dollar], sources
        )

        assert [r.asset_id for r in results] == [1]
        assert results[0].price == 101_452_240
