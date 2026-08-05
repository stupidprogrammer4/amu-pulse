import statistics
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Mapping, Sequence

from src.common.constants import TROY_OUNCE_GRAMS
from src.common.utils import currency_utils
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.calculator.domain.context import AssetContext
from src.modules.price.calculator.domain.results import (
    AssetPriceResult,
    BubbleResult,
)
from src.modules.price.engine.domain.results import SourcePriceResult
from src.modules.price.symbols.domain.enums import CurrencyType


class Aggregator:
    def _quantile(
        self,
        ordered: Sequence[int],
        share: float,
    ) -> float:
        """
        Desc: Read one quantile off an already sorted series.
        Args:
            ordered (Sequence[int]): The series, smallest first.
            share (float): Where to cut it, as a share of its length.
        Returns:
            return (float): The value sitting at that cut.
        """
        position = (len(ordered) - 1) * share
        low = int(position)
        high = min(low + 1, len(ordered) - 1)
        step = ordered[high] - ordered[low]
        value = ordered[low] + step * (position - low)
        return value

    def pick(
        self,
        values: Sequence[int],
        agg: AggregationType,
    ) -> int:
        """
        Desc: Fold a series of rial amounts by the rule it is folded with.
        Args:
            values (Sequence[int]): The amounts, in rial.
            agg (AggregationType): The rule to fold them by.
        Returns:
            return (int): The folded amount, rounded to the ten it sits on.
        """
        # the column is plain text, so a config row hands back a str
        rule = AggregationType(agg)
        ordered = sorted(values)
        picked: float = statistics.median(ordered)
        if rule is AggregationType.MEAN:
            picked = statistics.fmean(ordered)
        elif rule is AggregationType.MIN:
            picked = ordered[0]
        elif rule is AggregationType.MAX:
            picked = ordered[-1]
        elif rule is AggregationType.FIRST_QUARTILE:
            picked = self._quantile(ordered, 0.25)
        elif rule is AggregationType.THIRD_QUARTILE:
            picked = self._quantile(ordered, 0.75)
        return currency_utils.round_rial(picked)


class AbstractMarketCalculator(ABC):
    # a reading this far off the median is a source printing nonsense
    outlier_rate = 0.1
    # with two readings there is no crowd to be the odd one out of
    min_outlier_sample = 3

    def __init__(self) -> None:
        """
        Desc: Build the calculator with the rule it folds readings by.
        """
        self.aggregator = Aggregator()

    def _restated(
        self,
        reading: SourcePriceResult,
        buying: int,
        selling: int,
    ) -> SourcePriceResult:
        """
        Desc: Copy a reading with its two sides restated in rial per gram.
        Args:
            reading (SourcePriceResult): What the source quoted.
            buying (int): The buying side, in rial per gram.
            selling (int): The selling side, in rial per gram.
        Returns:
            return (SourcePriceResult): The restated reading; only its two
                sides and mid are meant to be read, the fold recomputes the
                rest.
        """
        restated = reading.model_copy(
            update={
                "currency": CurrencyType.RIAL,
                "buy_price": buying,
                "sell_price": selling,
                "price": currency_utils.round_rial((buying + selling) / 2),
            }
        )
        return restated

    def _kept(
        self,
        readings: Sequence[SourcePriceResult],
    ) -> Sequence[SourcePriceResult]:
        """
        Desc: Drop the readings sitting too far from what the rest agree on.
        Args:
            readings (Sequence[SourcePriceResult]): The restated readings.
        Returns:
            return (Sequence[SourcePriceResult]): The readings worth
                folding, all of them while the sample is too small to judge.
        """
        kept = list(readings)
        if len(kept) >= self.min_outlier_sample:
            middle = statistics.median([row.price for row in kept])
            if middle:
                gap = middle * self.outlier_rate
                kept = [row for row in kept if abs(row.price - middle) <= gap]
        return kept

    def _fold(
        self,
        asset: AssetContext,
        readings: Sequence[SourcePriceResult],
    ) -> AssetPriceResult | None:
        """
        Desc: Fold one market's restated readings into the asset's price.
        Args:
            asset (AssetContext): The asset being priced, with the rule its
                readings are folded by.
            readings (Sequence[SourcePriceResult]): The readings, already in
                rial per gram.
        Returns:
            return (AssetPriceResult | None): The asset's price, or None
                when that market quoted nothing for it.
        """
        result = None
        kept = self._kept(readings)
        if kept:
            agg = asset.config.agg_type
            buying = self.aggregator.pick([row.buy_price for row in kept], agg)
            selling = self.aggregator.pick(
                [row.sell_price for row in kept], agg
            )
            price = currency_utils.round_rial((buying + selling) / 2)
            divisor = price or 1
            buy_spread = price - buying
            sell_spread = selling - price
            result = AssetPriceResult(
                asset_id=asset.asset_id,
                buy_price=buying,
                sell_price=selling,
                price=price,
                buy_spread=buy_spread,
                sell_spread=sell_spread,
                buy_spread_rate=buy_spread / divisor,
                sell_spread_rate=sell_spread / divisor,
                priced_at=max(row.priced_at for row in kept),
            )
        return result


class AbstractLocalMarketCalculator(AbstractMarketCalculator):
    @abstractmethod
    def calculate(
        self,
        asset: AssetContext,
        sources: Sequence[SourcePriceResult],
    ) -> AssetPriceResult | None:
        """
        Desc: Fold what this market quoted into the asset's price.
        Args:
            asset (AssetContext): The asset being priced.
            sources (Sequence[SourcePriceResult]): That asset's readings
                from this market.
        Returns:
            return (AssetPriceResult | None): The asset's price, or None
                when the market quoted nothing for it.
        """
        ...

    def calculate_all(
        self,
        assets: Sequence[AssetContext],
        sources: Mapping[int, Sequence[SourcePriceResult]],
    ) -> Sequence[AssetPriceResult]:
        """
        Desc: Fold this market's readings for several assets.
        Args:
            assets (Sequence[AssetContext]): The assets being priced.
            sources (Mapping[int, Sequence[SourcePriceResult]]): Each
                asset's readings, keyed by asset id.
        Returns:
            return (Sequence[AssetPriceResult]): The prices of the assets
                the market quoted, in the order they were given.
        """
        results = []
        for asset in assets:
            result = self.calculate(asset, sources.get(asset.asset_id, ()))
            if result is not None:
                results.append(result)
        return results


class IranMarketCalculator(AbstractLocalMarketCalculator):
    def calculate(
        self,
        asset: AssetContext,
        sources: Sequence[SourcePriceResult],
    ) -> AssetPriceResult | None:
        """
        Desc: Fold what the Iranian market quoted into the asset's price.
        Args:
            asset (AssetContext): The asset being priced.
            sources (Sequence[SourcePriceResult]): That asset's readings
                from the Iranian market.
        Returns:
            return (AssetPriceResult | None): The asset's price, or None
                when the market quoted nothing for it.
        """
        # an iranian feed already quotes the asset's own unit, in rial
        readings = [
            row for row in sources if row.currency is CurrencyType.RIAL
        ]
        result = self._fold(asset, readings)
        return result


class SupplierCalculator(AbstractLocalMarketCalculator):
    def calculate(
        self,
        asset: AssetContext,
        sources: Sequence[SourcePriceResult],
    ) -> AssetPriceResult | None:
        """
        Desc: Fold what the suppliers quoted into the asset's price.
        Args:
            asset (AssetContext): The asset being priced.
            sources (Sequence[SourcePriceResult]): That asset's readings
                from the suppliers.
        Returns:
            return (AssetPriceResult | None): The asset's price, or None
                when no supplier quoted it.
        """
        # a supplier quotes the mazane; everything downstream is per gram
        readings = [
            self._restated(
                row,
                currency_utils.from_mazane(row.buy_price),
                currency_utils.from_mazane(row.sell_price),
            )
            for row in sources
            if row.currency is CurrencyType.RIAL
        ]
        result = self._fold(asset, readings)
        return result


class GlobalMarketCalculator(AbstractMarketCalculator):
    # what one gram of the asset holds of what the world feed prices pure
    purities: Mapping[AssetCode, Decimal] = {
        AssetCode.GOLD18: Decimal("0.750")
    }

    def _per_gram(
        self,
        cents: int,
        purity: Decimal,
        usd_price: int,
    ) -> int:
        """
        Desc: Turn a world price per troy ounce into rial per gram.
        Args:
            cents (int): One side of the reading, in cents per troy ounce.
            purity (Decimal): What the asset holds of the priced metal.
            usd_price (int): What one dollar costs, in rial.
        Returns:
            return (int): That side, in rial per gram of the asset.
        """
        dollars = Decimal(cents) / 100 / TROY_OUNCE_GRAMS * purity
        rial = currency_utils.from_usd(dollars, usd_price)
        return rial

    def calculate(
        self,
        usd_price: int,
        bubble: BubbleResult | None,
        asset: AssetContext,
        sources: Sequence[SourcePriceResult],
    ) -> AssetPriceResult | None:
        """
        Desc: Price the asset off world parity, lifted by its premium.
        Args:
            usd_price (int): What one dollar costs, in rial.
            bubble (BubbleResult | None): The settled premium of the asset,
                None while nothing has settled one.
            asset (AssetContext): The asset being priced.
            sources (Sequence[SourcePriceResult]): That asset's readings
                from the world market.
        Returns:
            return (AssetPriceResult | None): The asset's price, or None
                when the world market cannot price it.
        """
        result = None
        purity = self.purities.get(asset.code)
        if purity is not None and usd_price > 0:
            premium = bubble.amount if bubble is not None else 0
            # the world quotes the pure metal; the premium is what the local
            # market pays over that parity
            readings = [
                self._restated(
                    row,
                    currency_utils.with_bubble(
                        self._per_gram(row.buy_price, purity, usd_price),
                        premium,
                    ),
                    currency_utils.with_bubble(
                        self._per_gram(row.sell_price, purity, usd_price),
                        premium,
                    ),
                )
                for row in sources
                if row.currency is CurrencyType.USD
            ]
            result = self._fold(asset, readings)
        return result

    def calculate_all(
        self,
        usd_price: int,
        bubbles: Mapping[int, BubbleResult],
        assets: Sequence[AssetContext],
        sources: Mapping[int, Sequence[SourcePriceResult]],
    ) -> Sequence[AssetPriceResult]:
        """
        Desc: Price several assets off world parity and their premiums.
        Args:
            usd_price (int): What one dollar costs, in rial.
            bubbles (Mapping[int, BubbleResult]): Each asset's settled
                premium, keyed by asset id.
            assets (Sequence[AssetContext]): The assets being priced.
            sources (Mapping[int, Sequence[SourcePriceResult]]): Each
                asset's readings, keyed by asset id.
        Returns:
            return (Sequence[AssetPriceResult]): The prices of the assets
                the world market can price, in the order they were given.
        """
        results = []
        for asset in assets:
            result = self.calculate(
                usd_price,
                bubbles.get(asset.asset_id),
                asset,
                sources.get(asset.asset_id, ()),
            )
            if result is not None:
                results.append(result)
        return results
