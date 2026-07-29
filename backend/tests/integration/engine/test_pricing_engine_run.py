from types import SimpleNamespace
from typing import cast

import httpx
import pytest

from src.common.constants import MAZANE_FACTOR
from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.engine.app.services import PricingEngineService
from src.modules.price.engine.domain.context import (
    AssetRefContext,
    CFGContext,
    SourceContext,
)
from src.modules.price.engine.domain.enums import QuoteKind
from src.modules.price.engine.domain.quotes import (
    ErrorQuote,
    IranSourceQuote,
    SourceQuote,
    SupplierSourceQuote,
)
from src.modules.price.engine.domain.results import SupplierComputation
from src.modules.price.engine.infra.cache import SourcePriceCache
from src.modules.price.engine.infra.gateways import iran_market
from src.modules.price.engine.infra.readers import AssetReader, SourceReader
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import (
    ErrorType,
    SourceCode,
    SourceSwitch,
)
from src.modules.price.sources.domain.models import SourceConfigModel
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from tests.unit.engine.test_asset_price_cache import _FakeRedis

_BOARD = {
    "current": {
        "tgju_gold_irg18": {"p": "197631000"},
        "tgju_gold_irg18_buy": {"p": "195925000"},
        "price_dollar_rl": {"p": "1,931,900"},
    }
}


@pytest.fixture(autouse=True)
def sealed_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep every crawl under test off the real internet."""

    async def _answer(self: object, *args: object, **kwargs: object):
        return httpx.Response(
            200,
            json={},
            request=httpx.Request("GET", "https://sealed.test"),
        )

    for method in ("request", "get", "post"):
        monkeypatch.setattr(httpx.AsyncClient, method, _answer)


def _engine(
    uow: PGUnitOfWork,
) -> tuple[PricingEngineService, SourcePriceCache]:
    """
    Desc: Build the crawler over real readers and a fake-backed cache.
    Args:
        uow (PGUnitOfWork): Unit of work the readers query through.
    Returns:
        return (tuple[PricingEngineService, SourcePriceCache]): The service
            and the cache it writes to.
    """
    cache = SourcePriceCache(
        cast(RedisClient, SimpleNamespace(client=_FakeRedis()))
    )
    engine = PricingEngineService(AssetReader(uow), SourceReader(uow), cache)
    return engine, cache


def _pin_tgju(monkeypatch: pytest.MonkeyPatch, payload: object) -> None:
    """
    Desc: Answer every TGJU call with a canned board.
    Args:
        monkeypatch (pytest.MonkeyPatch): The patcher.
        payload (object): The JSON body to answer with.
    """

    async def _request(self: object, client: object) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", "https://example.test"),
        )

    monkeypatch.setattr(iran_market.TgjuFetcher, "_request", _request)


def _context(source_id: int = 7, asset_id: int = 3) -> CFGContext:
    """
    Desc: Build a crawl context naming one source and one asset.
    Args:
        source_id (int): ID the quoting source resolves to.
        asset_id (int): ID the quoted asset resolves to.
    Returns:
        return (CFGContext): The context.
    """
    return CFGContext(
        sources=[
            SourceContext(
                code=SourceCode.TGJU,
                id=source_id,
                switch=SourceSwitch.IRAN_MARKET,
                cfg=SourceConfigModel(source_id=source_id, timeout=5),
            )
        ],
        assets=[AssetRefContext(code=AssetCode.GOLD18, id=asset_id)],
    )


def _quote(
    selling: int = 197_631_000,
    buying: int = 195_925_000,
    error: ErrorQuote | None = None,
) -> SourceQuote:
    """
    Desc: Build a crawl result holding one Iranian gold quote.
    Args:
        selling (int): The quoted selling side.
        buying (int): The quoted buying side.
        error (ErrorQuote | None): The failure it carries, if any.
    Returns:
        return (SourceQuote): The crawl result.
    """
    return SourceQuote(
        irans=[
            IranSourceQuote(
                code=SourceCode.TGJU,
                asset=AssetCode.GOLD18,
                selling=selling,
                buying=buying,
                error=error,
            )
        ],
        globals=[],
        suppliers=[],
        bubbles=[],
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSaveAll:
    async def test_it_caches_a_quote_under_its_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)

        saved = await engine._save_all(_context(), _quote())

        cached = await cache.get(AssetCode.GOLD18)
        assert saved == 1
        assert cached is not None
        assert cached[0].source_id == 7
        assert cached[0].asset_id == 3

    async def test_it_prices_the_mid_and_both_spreads(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)

        await engine._save_all(
            _context(), _quote(selling=1_010_000, buying=990_000)
        )

        cached = await cache.get(AssetCode.GOLD18)
        assert cached is not None
        reading = cached[0]
        assert reading.price == 1_000_000
        assert reading.sell_price == 1_010_000
        assert reading.buy_price == 990_000
        assert reading.sell_spread_rial == 10_000
        assert reading.buy_spread_rial == 10_000

    async def test_a_failed_quote_is_not_cached(
        self, uow: PGUnitOfWork
    ) -> None:
        # a zero-priced error row would read as a source quoting a free gram
        engine, cache = _engine(uow)
        error = ErrorQuote(
            error_type=ErrorType.HTTP_ERROR, message="503", http_error=None
        )

        saved = await engine._save_all(
            _context(), _quote(selling=0, buying=0, error=error)
        )

        assert saved == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_a_quote_for_an_unknown_source_is_dropped(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)
        context = CFGContext(sources=[], assets=_context().assets)

        saved = await engine._save_all(context, _quote())

        assert saved == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_a_quote_for_an_unseeded_asset_is_dropped(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)
        context = CFGContext(sources=_context().sources, assets=[])

        saved = await engine._save_all(context, _quote())

        assert saved == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_a_crawl_that_quoted_nothing_writes_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)
        empty = SourceQuote(irans=[], globals=[], suppliers=[], bubbles=[])

        saved = await engine._save_all(_context(), empty)

        assert saved == 0
        assert await cache.get_all() == {}


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSaveSuppliers:
    async def test_a_mazane_is_cached_as_a_per_gram_gold_price(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)
        quote = SourceQuote(
            irans=[],
            globals=[],
            suppliers=[
                SupplierSourceQuote(
                    code=SourceCode.TALALAND,
                    asset=AssetCode.GOLD18,
                    kind=QuoteKind.MAZANE,
                    selling=4_331_802,
                    buying=4_331_802,
                )
            ],
            bubbles=[],
        )
        context = CFGContext(
            sources=[
                SourceContext(
                    code=SourceCode.TALALAND,
                    id=9,
                    switch=SourceSwitch.SUPPLIER,
                    cfg=SourceConfigModel(source_id=9, timeout=5),
                )
            ],
            assets=[AssetRefContext(code=AssetCode.GOLD18, id=3)],
        )

        saved = await engine._save_all(context, quote)

        cached = await cache.get(AssetCode.GOLD18)
        assert saved == 1
        assert cached is not None
        assert cached[0].price == 1_000_000
        assert cached[0].asset_id == 3

    async def test_it_carries_the_working_that_produced_it(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)
        quote = SourceQuote(
            irans=[],
            globals=[],
            suppliers=[
                SupplierSourceQuote(
                    code=SourceCode.TALALAND,
                    asset=AssetCode.GOLD18,
                    kind=QuoteKind.MAZANE,
                    selling=4_331_802,
                    buying=4_244_166,
                )
            ],
            bubbles=[],
        )
        context = CFGContext(
            sources=[
                SourceContext(
                    code=SourceCode.TALALAND,
                    id=9,
                    switch=SourceSwitch.SUPPLIER,
                    cfg=SourceConfigModel(source_id=9, timeout=5),
                )
            ],
            assets=[AssetRefContext(code=AssetCode.GOLD18, id=3)],
        )

        await engine._save_all(context, quote)

        cached = await cache.get(AssetCode.GOLD18)
        assert cached is not None
        working = cached[0].computation
        assert isinstance(working, SupplierComputation)
        # both sides are kept, so the per-gram price stays re-derivable
        assert working.selling_mazane == 4_331_802
        assert working.buying_mazane == 4_244_166
        assert working.mazane_factor == MAZANE_FACTOR
        assert working.final_price == 989_884

    async def test_a_supplier_reading_needs_the_gold_asset_seeded(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)
        quote = SourceQuote(
            irans=[],
            globals=[],
            suppliers=[
                SupplierSourceQuote(
                    code=SourceCode.TALALAND,
                    asset=AssetCode.GOLD18,
                    kind=QuoteKind.MAZANE,
                    selling=4_331_802,
                    buying=4_331_802,
                )
            ],
            bubbles=[],
        )
        context = CFGContext(
            sources=[
                SourceContext(
                    code=SourceCode.TALALAND,
                    id=9,
                    switch=SourceSwitch.SUPPLIER,
                    cfg=SourceConfigModel(source_id=9, timeout=5),
                )
            ],
            assets=[],
        )

        saved = await engine._save_all(context, quote)

        assert saved == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_an_iranian_reading_carries_no_working(
        self, uow: PGUnitOfWork
    ) -> None:
        # a rial feed quotes outright; there is nothing to show
        engine, cache = _engine(uow)

        await engine._save_all(_context(), _quote())

        cached = await cache.get(AssetCode.GOLD18)
        assert cached is not None
        assert cached[0].computation is None


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestRun:
    async def test_it_crawls_and_caches_end_to_end(
        self, uow: PGUnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin_tgju(monkeypatch, _BOARD)
        configs = AssetConfigService(AssetConfigRepository(uow))
        assets = AssetService(AssetRepository(uow), configs)
        sources = SourceService(
            SourceRepository(uow),
            SourceConfigService(SourceConfigRepository(uow)),
        )
        gold = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )
        usd = await assets.create(
            AssetCreate(title="دلار", code=AssetCode.USD)
        )
        source = await sources.create(
            SourceCreate(
                title="تجو",
                code=SourceCode.TGJU,
                website_url="https://www.tgju.org",
                icon_url="/storage/file/ab/x.png",
                primary_color="#c8a44b",
                source_type=SourceSwitch.IRAN_MARKET,
            )
        )
        engine, cache = _engine(uow)

        saved = await engine.run()

        board = await cache.get_all()
        assert saved == 2
        assert set(board) == {AssetCode.GOLD18, AssetCode.USD}
        assert board[AssetCode.GOLD18][0].asset_id == gold.id
        assert board[AssetCode.GOLD18][0].source_id == source.id
        assert board[AssetCode.USD][0].asset_id == usd.id
        assert board[AssetCode.GOLD18][0].price == 196_778_000

    async def test_an_empty_database_caches_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        engine, cache = _engine(uow)

        saved = await engine.run()

        assert saved == 0
        assert await cache.get_all() == {}
