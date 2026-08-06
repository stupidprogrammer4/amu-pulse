import pytest

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.domain.models import (
    CandleModel,
    SourceCandleModel,
)
from src.modules.chart.candle.infra.repository import (
    CandleRepository,
    SourceCandleRepository,
)
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.domain.dtos import SymbolCreate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.domain.models import SymbolModel
from src.modules.price.symbols.infra.repository import SymbolRepository
from tests.conftest import NullScheduler

_st_ts = 1_785_000_000
_five_minutes = 5 * 60


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(
        AssetCreate(title="طلا", code=code, primary_color="#c8a44b")
    )
    return asset


async def _symbol(
    uow: PGUnitOfWork,
    asset: AssetModel,
    code: SymbolCode = SymbolCode.GOLD18_GRAM,
) -> SymbolModel:
    symbols = SymbolService(SymbolRepository(uow))
    symbol = await symbols.create(
        SymbolCreate(
            title="هر گرم",
            code=code,
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=CurrencyType.RIAL,
            primary_color="#c8a44b",
        )
    )
    return symbol


async def _source(
    uow: PGUnitOfWork,
    code: SourceCode = SourceCode.TGJU,
) -> SourceModel:
    configs = SourceConfigService(SourceConfigRepository(uow))
    sources = SourceService(SourceRepository(uow), configs)
    source = await sources.create(
        SourceCreate(
            title="منبع",
            code=code,
            website_url="https://example.test",
            icon_url="/storage/file/ab/x.png",
            primary_color="#4b8ec8",
            source_type=SourceSwitch.IRAN_MARKET,
        )
    )
    return source


def _candle(
    asset: AssetModel,
    st_ts: int,
    close: int,
    timeframe: TimeFrame = TimeFrame.FIVE_MINUTE,
) -> CandleModel:
    return CandleModel(
        asset_id=asset.id,
        timeframe=timeframe,
        open=100,
        high=max(100, close),
        low=min(100, close),
        close=close,
        st_ts=st_ts,
        en_ts=st_ts + timeframe.seconds,
    )


def _source_candle(
    source: SourceModel,
    symbol: SymbolModel,
    st_ts: int,
    close: int,
    timeframe: TimeFrame = TimeFrame.FIVE_MINUTE,
) -> SourceCandleModel:
    return SourceCandleModel(
        source_id=source.id,
        symbol_id=symbol.id,
        timeframe=timeframe,
        open=100,
        high=max(100, close),
        low=min(100, close),
        close=close,
        st_ts=st_ts,
        en_ts=st_ts + timeframe.seconds,
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestWritingAssetCandles:
    async def test_a_written_candle_reads_back(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)

        await repo.bulk_upsert([_candle(asset, _st_ts, 140)])
        found = await repo.get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, _st_ts, _st_ts + _five_minutes
        )

        assert len(found) == 1
        assert (found[0].open, found[0].high, found[0].close) == (
            100,
            140,
            140,
        )

    async def test_the_candles_come_back_oldest_first(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)
        stamps = [_st_ts + step * _five_minutes for step in (2, 0, 1)]

        await repo.bulk_upsert(
            [_candle(asset, stamp, 100) for stamp in stamps]
        )
        found = await repo.get_by_timeframe(
            asset.id,
            TimeFrame.FIVE_MINUTE,
            _st_ts,
            _st_ts + 3 * _five_minutes,
        )

        assert [row.st_ts for row in found] == sorted(stamps)

    async def test_a_rerun_rewrites_the_candle_it_already_wrote(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)

        await repo.bulk_upsert([_candle(asset, _st_ts, 140)])
        await repo.bulk_upsert([_candle(asset, _st_ts, 90)])
        found = await repo.get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, _st_ts, _st_ts + _five_minutes
        )

        assert len(found) == 1
        assert (found[0].low, found[0].close) == (90, 90)

    async def test_another_asset_keeps_its_own_candle(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        usd = await _asset(uow, AssetCode.USD)
        repo = CandleRepository(uow)

        await repo.bulk_upsert(
            [_candle(gold, _st_ts, 140), _candle(usd, _st_ts, 90)]
        )
        found = await repo.get_by_timeframe(
            gold.id, TimeFrame.FIVE_MINUTE, _st_ts, _st_ts + _five_minutes
        )

        assert [row.asset_id for row in found] == [gold.id]

    async def test_the_same_window_of_another_timeframe_is_its_own_candle(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)

        await repo.bulk_upsert(
            [
                _candle(asset, _st_ts, 140),
                _candle(asset, _st_ts, 90, TimeFrame.HOURLY),
            ]
        )
        found = await repo.get_by_timeframe(
            asset.id, TimeFrame.HOURLY, _st_ts, _st_ts + _five_minutes
        )

        assert len(found) == 1
        assert found[0].close == 90


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestReadingAssetCandlesOverARange:
    async def test_the_candle_the_range_opens_on_is_read(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)

        await repo.bulk_upsert([_candle(asset, _st_ts, 100)])
        found = await repo.get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, _st_ts, _st_ts + _five_minutes
        )

        assert [row.st_ts for row in found] == [_st_ts]

    async def test_the_candle_the_range_closes_on_is_left(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)
        closing = _st_ts + _five_minutes

        await repo.bulk_upsert([_candle(asset, closing, 100)])
        found = await repo.get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, _st_ts, closing
        )

        assert found == []

    async def test_a_candle_before_the_range_is_left(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)

        await repo.bulk_upsert([_candle(asset, _st_ts - _five_minutes, 100)])
        found = await repo.get_by_timeframe(
            asset.id, TimeFrame.FIVE_MINUTE, _st_ts, _st_ts + _five_minutes
        )

        assert found == []

    async def test_every_asset_comes_back_grouped_and_oldest_first(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        usd = await _asset(uow, AssetCode.USD)
        repo = CandleRepository(uow)
        later = _st_ts + _five_minutes

        await repo.bulk_upsert(
            [
                _candle(gold, later, 140),
                _candle(usd, later, 90),
                _candle(gold, _st_ts, 100),
                _candle(usd, _st_ts, 100),
            ]
        )
        found = await repo.get_all_by_timeframe(
            TimeFrame.FIVE_MINUTE, _st_ts, later + _five_minutes
        )

        assert [(row.asset_id, row.st_ts) for row in found] == [
            (gold.id, _st_ts),
            (gold.id, later),
            (usd.id, _st_ts),
            (usd.id, later),
        ]

    async def test_only_the_timeframe_asked_for_comes_back(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        repo = CandleRepository(uow)

        await repo.bulk_upsert(
            [
                _candle(asset, _st_ts, 140),
                _candle(asset, _st_ts, 90, TimeFrame.HOURLY),
            ]
        )
        found = await repo.get_all_by_timeframe(
            TimeFrame.HOURLY, _st_ts, _st_ts + _five_minutes
        )

        assert [row.timeframe for row in found] == [TimeFrame.HOURLY]


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceCandles:
    async def test_a_written_candle_reads_back(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        repo = SourceCandleRepository(uow)

        await repo.bulk_upsert([_source_candle(source, symbol, _st_ts, 140)])
        found = await repo.get_by_timeframe(
            source.id,
            symbol.id,
            TimeFrame.FIVE_MINUTE,
            _st_ts,
            _st_ts + _five_minutes,
        )

        assert len(found) == 1
        assert (found[0].high, found[0].close) == (140, 140)

    async def test_a_rerun_rewrites_the_candle_it_already_wrote(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        repo = SourceCandleRepository(uow)

        await repo.bulk_upsert([_source_candle(source, symbol, _st_ts, 140)])
        await repo.bulk_upsert([_source_candle(source, symbol, _st_ts, 90)])
        found = await repo.get_by_timeframe(
            source.id,
            symbol.id,
            TimeFrame.FIVE_MINUTE,
            _st_ts,
            _st_ts + _five_minutes,
        )

        assert len(found) == 1
        assert found[0].close == 90

    async def test_another_source_keeps_its_own_candle(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        tgju = await _source(uow)
        alanchand = await _source(uow, SourceCode.ALANCHAND)
        repo = SourceCandleRepository(uow)

        await repo.bulk_upsert(
            [
                _source_candle(tgju, symbol, _st_ts, 140),
                _source_candle(alanchand, symbol, _st_ts, 90),
            ]
        )
        found = await repo.get_by_timeframe(
            tgju.id,
            symbol.id,
            TimeFrame.FIVE_MINUTE,
            _st_ts,
            _st_ts + _five_minutes,
        )

        assert [row.source_id for row in found] == [tgju.id]

    async def test_another_line_of_the_same_source_is_left(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        gram = await _symbol(uow, asset)
        mazane = await _symbol(uow, asset, SymbolCode.GOLD18_MAZANE)
        source = await _source(uow)
        repo = SourceCandleRepository(uow)

        await repo.bulk_upsert(
            [
                _source_candle(source, gram, _st_ts, 140),
                _source_candle(source, mazane, _st_ts, 90),
            ]
        )
        found = await repo.get_by_timeframe(
            source.id,
            gram.id,
            TimeFrame.FIVE_MINUTE,
            _st_ts,
            _st_ts + _five_minutes,
        )

        assert [row.symbol_id for row in found] == [gram.id]

    async def test_every_source_and_line_comes_back_grouped(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        gram = await _symbol(uow, asset)
        mazane = await _symbol(uow, asset, SymbolCode.GOLD18_MAZANE)
        tgju = await _source(uow)
        alanchand = await _source(uow, SourceCode.ALANCHAND)
        repo = SourceCandleRepository(uow)
        later = _st_ts + _five_minutes

        await repo.bulk_upsert(
            [
                _source_candle(alanchand, gram, _st_ts, 90),
                _source_candle(tgju, mazane, later, 140),
                _source_candle(tgju, gram, later, 140),
                _source_candle(tgju, gram, _st_ts, 100),
            ]
        )
        found = await repo.get_all_by_timeframe(
            TimeFrame.FIVE_MINUTE, _st_ts, later + _five_minutes
        )

        assert [
            (row.source_id, row.symbol_id, row.st_ts) for row in found
        ] == [
            (tgju.id, gram.id, _st_ts),
            (tgju.id, gram.id, later),
            (tgju.id, mazane.id, later),
            (alanchand.id, gram.id, _st_ts),
        ]
