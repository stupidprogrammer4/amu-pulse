from typing import Protocol, Sequence

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import (
    AssetPriceResult,
    BubbleResult,
)


class ICalculatorService(Protocol):
    async def calculate_all(self) -> int: ...

    async def calculate_usd(self) -> int: ...

    async def calculate(self, asset_id: int) -> int: ...


class IBubbleCalculatorService(Protocol):
    async def calculate_all(self) -> int: ...

    async def calculate(self, bubble_id: int) -> int: ...


class ICacheReaderService(Protocol):
    async def get_price(
        self, asset_code: AssetCode
    ) -> AssetPriceResult | None: ...

    async def get_bubble_amount(
        self, bubble_code: AssetCode
    ) -> BubbleResult | None: ...

    async def get_all_bubble_amounts(self) -> Sequence[BubbleResult]: ...

    async def get_all_prices(self) -> Sequence[AssetPriceResult]: ...
