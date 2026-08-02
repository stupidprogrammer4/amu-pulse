from datetime import UTC, datetime
from typing import Sequence, cast

from src.modules.chart.ticker.app.services import (
    PriceSnapshotService,
    SourcePriceSnapshotService,
)
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.domain.results import (
    AssetPriceResult,
    BubbleResult,
)
from src.modules.price.calculator.interfaces import (
    ICacheReaderService as IPriceCacheReaderService,
)
from src.modules.price.engine.domain.results import (
    SourceBubbleResult,
    SourcePriceResult,
)
from src.modules.price.engine.interfaces import (
    ICacheReaderService as IReadingCacheReaderService,
)
from src.modules.price.symbols.domain.enums import CurrencyType

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
_epoch = int(_at.timestamp())


class _FakeRepo:
    """The one write a snapshot makes."""

    def __init__(self) -> None:
        self.written: list = []

    async def bulk_create(self, data: Sequence) -> Sequence:
        self.written.extend(data)
        return data


class _FakePriceCacheReader:
    """The price side of the calculator's cache reader."""

    def __init__(self, prices: Sequence[AssetPriceResult]) -> None:
        self.prices = prices

    async def get_all_prices(self) -> Sequence[AssetPriceResult]:
        return self.prices

    async def get_price(
        self, asset_code: AssetCode
    ) -> AssetPriceResult | None:
        return None

    async def get_bubble_amount(
        self, bubble_code: AssetCode
    ) -> BubbleResult | None:
        return None

    async def get_all_bubble_amounts(self) -> Sequence[BubbleResult]:
        return []


class _FakeReadingCacheReader:
    """The reading side of the engine's cache reader."""

    def __init__(self, board: dict) -> None:
        self.board = board

    async def get_all(self) -> dict:
        return dict(self.board)

    async def get_by_symbol(self, symbol) -> Sequence[SourcePriceResult]:
        return self.board.get(symbol, [])

    async def get_many_by_symbols(self, symbols) -> dict:
        return {code: self.board[code] for code in symbols}

    async def get_bubbles_by_asset(
        self, code: AssetCode
    ) -> Sequence[SourceBubbleResult]:
        return []

    async def get_all_bubbles(self) -> dict:
        return {}


def _price(asset_id: int, price: int) -> AssetPriceResult:
    """
    Desc: Build one cached asset price.
    Args:
        asset_id (int): ID of the asset it belongs to.
        price (int): The mid price in rial.
    Returns:
        return (AssetPriceResult): The price.
    """
    return AssetPriceResult(
        asset_id=asset_id,
        buy_price=price,
        sell_price=price,
        price=price,
        buy_spread=0,
        sell_spread=0,
        buy_spread_rate=0.0,
        sell_spread_rate=0.0,
        priced_at=_at,
    )


def _reading(source_id: int, symbol_id: int, price: int):
    """
    Desc: Build one cached source reading.
    Args:
        source_id (int): ID of the source that quoted it.
        symbol_id (int): ID of the line it was quoted for.
        price (int): The mid price in rial.
    Returns:
        return (SourcePriceResult): The reading.
    """
    return SourcePriceResult(
        source_id=source_id,
        symbol_id=symbol_id,
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


class TestPriceSnapshot:
    async def test_every_priced_asset_is_written_down(self) -> None:
        repo = _FakeRepo()
        service = PriceSnapshotService(
            cast(PriceTickerRepository, repo),
            cast(
                IPriceCacheReaderService,
                _FakePriceCacheReader([_price(1, 100), _price(2, 200)]),
            ),
        )

        written = await service.snapshot_all()

        assert written is True
        assert [row.asset_id for row in repo.written] == [1, 2]
        assert [row.price for row in repo.written] == [100, 200]

    async def test_the_point_carries_the_time_it_was_priced_at(
        self,
    ) -> None:
        repo = _FakeRepo()
        service = PriceSnapshotService(
            cast(PriceTickerRepository, repo),
            cast(
                IPriceCacheReaderService,
                _FakePriceCacheReader([_price(1, 100)]),
            ),
        )

        await service.snapshot_all()

        row = cast(PriceTickerModel, repo.written[0])
        assert row.timestamp == _epoch

    async def test_an_empty_board_writes_nothing(self) -> None:
        repo = _FakeRepo()
        service = PriceSnapshotService(
            cast(PriceTickerRepository, repo),
            cast(IPriceCacheReaderService, _FakePriceCacheReader([])),
        )

        written = await service.snapshot_all()

        assert written is False
        assert repo.written == []


class TestSourcePriceSnapshot:
    async def test_every_reading_is_written_under_its_asset(self) -> None:
        repo = _FakeRepo()
        service = SourcePriceSnapshotService(
            cast(SourcePriceTickerRepository, repo),
            cast(
                IReadingCacheReaderService,
                _FakeReadingCacheReader(
                    {
                        "gold18_gram": [
                            _reading(12, 1, 100),
                            _reading(13, 1, 101),
                        ],
                        "usd_rial": [_reading(12, 2, 1_900)],
                    }
                ),
            ),
        )

        written = await service.snapshot_all()

        assert written is True
        assert [row.source_id for row in repo.written] == [12, 13, 12]
        assert [row.symbol_id for row in repo.written] == [1, 1, 2]

    async def test_every_line_on_the_board_is_written_down(self) -> None:
        repo = _FakeRepo()
        service = SourcePriceSnapshotService(
            cast(SourcePriceTickerRepository, repo),
            cast(
                IReadingCacheReaderService,
                _FakeReadingCacheReader(
                    {
                        "gold18_gram": [_reading(12, 1, 100)],
                        "gold18_mazane": [_reading(13, 2, 4_331_802)],
                    }
                ),
            ),
        )

        written = await service.snapshot_all()

        assert written is True
        assert len(repo.written) == 2

    async def test_the_point_carries_the_time_it_was_quoted_at(
        self,
    ) -> None:
        repo = _FakeRepo()
        service = SourcePriceSnapshotService(
            cast(SourcePriceTickerRepository, repo),
            cast(
                IReadingCacheReaderService,
                _FakeReadingCacheReader(
                    {"gold18_gram": [_reading(12, 1, 100)]}
                ),
            ),
        )

        await service.snapshot_all()

        row = cast(SourcePriceTickerModel, repo.written[0])
        assert row.timestamp == _epoch
        assert row.price == 100

    async def test_an_empty_board_writes_nothing(self) -> None:
        repo = _FakeRepo()
        service = SourcePriceSnapshotService(
            cast(SourcePriceTickerRepository, repo),
            cast(IReadingCacheReaderService, _FakeReadingCacheReader({})),
        )

        written = await service.snapshot_all()

        assert written is False
