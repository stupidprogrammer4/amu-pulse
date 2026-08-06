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
    outlier_rate = 0.1
    min_outlier_sample = 3

    def __init__(self) -> None:
        self.aggregator = Aggregator()

    def _restated(
        self,
        reading: SourcePriceResult,
        buying: int,
        selling: int,
    ) -> SourcePriceResult:
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
        ...

    def calculate_all(
        self,
        assets: Sequence[AssetContext],
        sources: Mapping[int, Sequence[SourcePriceResult]],
    ) -> Sequence[AssetPriceResult]:
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
    purities: Mapping[AssetCode, Decimal] = {
        AssetCode.GOLD18: Decimal("0.750")
    }

    def _per_gram(
        self,
        cents: int,
        purity: Decimal,
        usd_price: int,
    ) -> int:
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
        result = None
        purity = self.purities.get(asset.code)
        if purity is not None and usd_price > 0:
            premium = bubble.amount if bubble is not None else 0
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
