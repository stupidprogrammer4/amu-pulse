import pytest

from src.common.utils import date_utils
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.chart.ticker.app.services import (
    PriceTickerService,
    SourcePriceTickerService,
)
from src.modules.chart.ticker.domain.enums import ChartType
from src.modules.chart.ticker.domain.models import (
    PriceTickerModel,
    SourcePriceTickerModel,
)
from src.modules.chart.ticker.infra.repository import (
    PriceTickerRepository,
    SourcePriceTickerRepository,
)
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetMetaService,
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
    SourceMetaService,
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

_minute = 60
_hour = 60 * _minute


def _now() -> int:
    """
    Desc: Read the moment the charts are measured back from.
    Returns:
        return (int): Now, in whole seconds.
    """
    return int(date_utils.utc_now().timestamp())


def _asset_meta(uow: PGUnitOfWork) -> AssetMetaService:
    """
    Desc: Build the asset meta service over real services.
    Args:
        uow (PGUnitOfWork): Unit of work to read through.
    Returns:
        return (AssetMetaService): The service that names an asset.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    return AssetMetaService(AssetService(AssetRepository(uow), configs))


def _source_meta(uow: PGUnitOfWork) -> SourceMetaService:
    """
    Desc: Build the source meta service over real services.
    Args:
        uow (PGUnitOfWork): Unit of work to read through.
    Returns:
        return (SourceMetaService): The service that names a source and a
            line.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    return SourceMetaService(
        SourceService(SourceRepository(uow), configs),
        SymbolService(SymbolRepository(uow)),
    )


def _prices(uow: PGUnitOfWork) -> PriceTickerService:
    """
    Desc: Build the asset chart service over the real table.
    Args:
        uow (PGUnitOfWork): Unit of work to read through.
    Returns:
        return (PriceTickerService): The service.
    """
    return PriceTickerService(PriceTickerRepository(uow), _asset_meta(uow))


def _sources(uow: PGUnitOfWork) -> SourcePriceTickerService:
    """
    Desc: Build the source chart service over the real table.
    Args:
        uow (PGUnitOfWork): Unit of work to read through.
    Returns:
        return (SourcePriceTickerService): The service.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    return SourcePriceTickerService(
        SourcePriceTickerRepository(uow),
        SourceService(SourceRepository(uow), configs),
        _source_meta(uow),
    )


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset to hang points off.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
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
    """
    Desc: Create the line an asset is quoted through.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the line belongs to.
        code (SymbolCode): Code of the line.
    Returns:
        return (SymbolModel): The created line.
    """
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
    """
    Desc: Create one source feeding the Iranian market.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (SourceCode): Code of the source.
    Returns:
        return (SourceModel): The created source.
    """
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


async def _points(
    uow: PGUnitOfWork,
    asset: AssetModel,
    points: list[tuple[int, int]],
) -> None:
    """
    Desc: Write one asset point per pair given.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the points belong to.
        points (list[tuple[int, int]]): The time and price of each point.
    """
    await PriceTickerRepository(uow).bulk_create(
        [
            PriceTickerModel(asset_id=asset.id, price=price, timestamp=stamp)
            for stamp, price in points
        ]
    )


async def _source_points(
    uow: PGUnitOfWork,
    symbol: SymbolModel,
    source: SourceModel,
    points: list[tuple[int, int]],
) -> None:
    """
    Desc: Write one source point per pair given.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        symbol (SymbolModel): The line the points were quoted for.
        source (SourceModel): The source that quoted them.
        points (list[tuple[int, int]]): The time and price of each point.
    """
    await SourcePriceTickerRepository(uow).bulk_create(
        [
            SourcePriceTickerModel(
                symbol_id=symbol.id,
                source_id=source.id,
                price=price,
                timestamp=stamp,
            )
            for stamp, price in points
        ]
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheAssetChart:
    async def test_it_draws_the_points_it_was_snapshotted_at(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await _points(
            uow,
            asset,
            [(now - 10 * _minute, 100), (now - 5 * _minute, 110)],
        )

        result = await _prices(uow).get_chart(asset.id, ChartType.DAILY)

        assert [point.price for point in result.data.points] == [100, 110]
        assert result.data.type is ChartType.DAILY
        assert result.data.to_timestamp - result.data.from_timestamp == (
            ChartType.DAILY.span
        )

    async def test_the_change_is_the_first_price_against_the_last(
        self, uow: PGUnitOfWork
    ) -> None:
        # 100 -> 110 is a tenth up, whatever happened in between
        asset = await _asset(uow)
        now = _now()
        await _points(
            uow,
            asset,
            [
                (now - 15 * _minute, 100),
                (now - 10 * _minute, 400),
                (now - 5 * _minute, 110),
            ],
        )

        result = await _prices(uow).get_chart(asset.id, ChartType.DAILY)

        assert result.data.change_rate == pytest.approx(0.1)

    async def test_a_fall_is_a_negative_change(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await _points(
            uow, asset, [(now - 10 * _minute, 200), (now - 5 * _minute, 150)]
        )

        result = await _prices(uow).get_chart(asset.id, ChartType.DAILY)

        assert result.data.change_rate == pytest.approx(-0.25)

    async def test_it_says_where_the_chart_sat(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        now = _now()
        await _points(
            uow,
            asset,
            [
                (now - 15 * _minute, 100),
                (now - 10 * _minute, 400),
                (now - 5 * _minute, 100),
            ],
        )

        result = await _prices(uow).get_chart(asset.id, ChartType.DAILY)

        assert result.data.max == 400
        assert result.data.min == 100
        assert result.data.mean == 200

    async def test_the_charted_asset_is_named(self, uow: PGUnitOfWork) -> None:
        asset = await _asset(uow)
        now = _now()
        await _points(uow, asset, [(now, 100)])

        result = await _prices(uow).get_chart(asset.id, ChartType.DAILY)

        assert [meta.id for meta in result.meta.assets] == [asset.id]
        assert result.meta.assets[0].code == AssetCode.GOLD18
        assert result.meta.assets[0].primary_color == "#c8a44b"

    async def test_an_asset_nobody_snapshotted(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)

        result = await _prices(uow).get_chart(asset.id, ChartType.DAILY)

        assert result.data.points == []
        assert result.data.change_rate == 0.0
        assert result.data.max == 0
        assert list(result.meta.assets) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestTheSourceChart:
    async def test_one_line_is_drawn_once_per_source(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        tgju = await _source(uow)
        alan = await _source(uow, SourceCode.ALANCHAND)
        now = _now()
        await _source_points(uow, symbol, tgju, [(now - _minute, 100)])
        await _source_points(uow, symbol, alan, [(now - _minute, 101)])

        result = await _sources(uow).get_chart_by_symbol(
            symbol.id, ChartType.DAILY
        )

        assert {
            code: [point.price for point in points]
            for code, points in result.data.source_points.items()
        } == {SourceCode.TGJU: [100], SourceCode.ALANCHAND: [101]}

    async def test_both_the_sources_and_the_line_are_named(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        now = _now()
        await _source_points(uow, symbol, source, [(now, 100)])

        result = await _sources(uow).get_chart_by_symbol(
            symbol.id, ChartType.DAILY
        )

        assert [meta.code for meta in result.meta.sources] == [SourceCode.TGJU]
        assert [meta.code for meta in result.meta.symbols] == [
            SymbolCode.GOLD18_GRAM
        ]

    async def test_a_line_nobody_quoted(self, uow: PGUnitOfWork) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)

        result = await _sources(uow).get_chart_by_symbol(
            symbol.id, ChartType.DAILY
        )

        assert result.data.source_points == {}
        assert list(result.meta.sources) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestOneSourceOnOneLine:
    async def test_it_draws_only_that_source(self, uow: PGUnitOfWork) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        tgju = await _source(uow)
        alan = await _source(uow, SourceCode.ALANCHAND)
        now = _now()
        await _source_points(uow, symbol, tgju, [(now - _minute, 100)])
        await _source_points(uow, symbol, alan, [(now - _minute, 999)])

        result = await _sources(uow).get_source_chart_by_symbol(
            tgju.id, symbol.id, ChartType.DAILY
        )

        assert [point.price for point in result.data.points] == [100]
        assert [meta.code for meta in result.meta.sources] == [SourceCode.TGJU]

    async def test_the_change_is_the_first_price_against_the_last(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)
        now = _now()
        await _source_points(
            uow,
            symbol,
            source,
            [(now - 2 * _hour, 100), (now - _hour, 120)],
        )

        result = await _sources(uow).get_source_chart_by_symbol(
            source.id, symbol.id, ChartType.DAILY
        )

        assert result.data.change_rate == pytest.approx(0.2)

    async def test_a_line_that_source_never_quoted(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        symbol = await _symbol(uow, asset)
        source = await _source(uow)

        result = await _sources(uow).get_source_chart_by_symbol(
            source.id, symbol.id, ChartType.DAILY
        )

        assert result.data.points == []
        assert result.data.change_rate == 0.0
