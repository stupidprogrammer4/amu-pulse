from datetime import UTC, datetime
from typing import Sequence, cast

import src.tasks.broker  # noqa: F401
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.results import (
    SourceBubbleResult,
    SourcePriceResult,
)
from src.modules.price.engine.interfaces import ICacheReaderService
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.modules.price.sources.domain.schemas import SymbolPricesOut
from src.modules.price.sources.routers import admin
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


class _FakeCacheReader:

    def __init__(
        self,
        readings: dict[SymbolCode, Sequence[SourcePriceResult]],
    ) -> None:
        self.readings = readings

    async def get_all(
        self,
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]:
        return dict(self.readings)

    async def get_by_symbol(
        self, symbol: SymbolCode
    ) -> Sequence[SourcePriceResult]:
        return self.readings.get(symbol, [])

    async def get_many_by_symbols(
        self, symbols: Sequence[SymbolCode]
    ) -> dict[SymbolCode, Sequence[SourcePriceResult]]:
        return {code: self.readings[code] for code in symbols}

    async def get_bubbles_by_asset(
        self, code: AssetCode
    ) -> Sequence[SourceBubbleResult]:
        return []

    async def get_all_bubbles(
        self,
    ) -> dict[AssetCode, Sequence[SourceBubbleResult]]:
        return {}


def _reading(source_id: int, price: int) -> SourcePriceResult:
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=1,
        currency=CurrencyType.RIAL,
        buy_price=price,
        sell_price=price,
        price=price,
        buy_spread=0,
        sell_spread=0,
        buy_spread_rate=0.0,
        sell_spread_rate=0.0,
        priced_at=_at,
    )


class TestGetSourcePrices:
    async def test_it_answers_with_the_whole_board(self) -> None:
        reader = _FakeCacheReader(
            {
                SymbolCode.GOLD18_GRAM: [
                    _reading(12, 100_000_000),
                    _reading(13, 101_000_000),
                ],
                SymbolCode.USD_RIAL: [_reading(12, 1_900_000)],
            }
        )

        response = await admin.get_source_prices(
            cast(ICacheReaderService, reader)
        )

        rows = cast(list[SymbolPricesOut], response.data)

        assert response.success is True
        assert [row.symbol for row in rows] == [
            SymbolCode.GOLD18_GRAM,
            SymbolCode.USD_RIAL,
        ]
        assert [len(row.prices) for row in rows] == [2, 1]

    async def test_the_source_id_leaves_encoded(self) -> None:
        reader = _FakeCacheReader(
            {SymbolCode.GOLD18_GRAM: [_reading(12, 100_000_000)]}
        )

        response = await admin.get_source_prices(
            cast(ICacheReaderService, reader)
        )
        dumped = response.model_dump()

        assert dumped["data"][0]["prices"][0][
            "source_id"
        ] == SOURCE_ID_ENCRYPTION.encode(12)

    async def test_a_board_the_crawl_never_filled(self) -> None:
        reader = _FakeCacheReader({})

        response = await admin.get_source_prices(
            cast(ICacheReaderService, reader)
        )

        assert response.data == []
