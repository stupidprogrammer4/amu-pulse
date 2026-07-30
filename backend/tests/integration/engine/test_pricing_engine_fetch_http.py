from types import SimpleNamespace
from typing import cast

import httpx
import pytest

from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.price.engine.app.services import PricingEngineService
from src.modules.price.engine.domain.context import CFGContext, SourceContext
from src.modules.price.engine.infra.cache import (
    BubbleCache,
    BubbleSourceCache,
    SourcePriceCache,
)
from src.modules.price.engine.infra.gateways import iran_market
from src.modules.price.engine.infra.readers import (
    AssetReader,
    SourceReader,
    SymbolReader,
)
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceConfigModel
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.modules.price.symbols.domain.enums import SymbolCode
from tests.unit.engine.test_asset_price_cache import _FakeRedis


def _engine(uow: PGUnitOfWork) -> PricingEngineService:
    """
    Desc: Build the crawler over real readers.
    Args:
        uow (PGUnitOfWork): Unit of work the readers query through.
    Returns:
        return (PricingEngineService): The assembled service.
    """
    # these cover the read and crawl halves; nothing here writes, so the
    # cache is stood up over a fake rather than a live Redis
    client = cast(RedisClient, SimpleNamespace(client=_FakeRedis()))
    return PricingEngineService(
        AssetReader(uow),
        SymbolReader(uow),
        SourceReader(uow),
        SourcePriceCache(client),
        BubbleCache(client),
        BubbleSourceCache(client),
    )


def _sources(uow: PGUnitOfWork) -> SourceService:
    """
    Desc: Build the source service over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (SourceService): The assembled service.
    """
    return SourceService(
        SourceRepository(uow), SourceConfigService(SourceConfigRepository(uow))
    )


def _source_data(code: SourceCode, switch: SourceSwitch) -> SourceCreate:
    """
    Desc: Build a SourceCreate DTO for the given code and market.
    Args:
        code (SourceCode): Code of the source.
        switch (SourceSwitch): The market it feeds.
    Returns:
        return (SourceCreate): The create DTO.
    """
    return SourceCreate(
        title="منبع",
        code=code,
        website_url="https://example.test",
        icon_url="/storage/file/ab/x.png",
        primary_color="#c8a44b",
        source_type=switch,
    )


def _context(*sources: SourceContext) -> CFGContext:
    """
    Desc: Build a crawl context out of the given sources.
    Args:
        sources (SourceContext): The sources to crawl.
    Returns:
        return (CFGContext): The context.
    """
    return CFGContext(sources=list(sources), symbols=[], assets=[])


def _source_context(
    code: SourceCode,
    switch: SourceSwitch = SourceSwitch.IRAN_MARKET,
) -> SourceContext:
    """
    Desc: Build a source context without touching the database.
    Args:
        code (SourceCode): Code of the source.
        switch (SourceSwitch): The market it feeds.
    Returns:
        return (SourceContext): The context.
    """
    return SourceContext(
        code=code,
        id=1,
        switch=switch,
        cfg=SourceConfigModel(source_id=1, timeout=5),
    )


def _pin(monkeypatch: pytest.MonkeyPatch, payload: object) -> None:
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


_BOARD = {
    "current": {
        "tgju_gold_irg18": {"p": "197631000"},
        "tgju_gold_irg18_buy": {"p": "195925000"},
        "price_dollar_rl": {"p": "1,931,900"},
    }
}


@pytest.fixture(autouse=True)
def sealed_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Answer every outbound call from here, so a crawl under test never
    reaches a real source. A body no fetcher can parse is fine: it still
    comes back as one quote per fetcher, carrying its error."""

    async def _answer(self: object, *args: object, **kwargs: object):
        return httpx.Response(
            200,
            json={},
            request=httpx.Request("GET", "https://sealed.test"),
        )

    for method in ("request", "get", "post"):
        monkeypatch.setattr(httpx.AsyncClient, method, _answer)


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestFetchAllHTTP:
    async def test_it_calls_a_source_and_returns_its_quotes(
        self, uow: PGUnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin(monkeypatch, _BOARD)
        context = _context(_source_context(SourceCode.TGJU))

        quote = await _engine(uow)._fetch_all_http(context)

        assert {q.symbol for q in quote.irans} == {
            SymbolCode.GOLD18_GRAM,
            SymbolCode.USD_RIAL,
        }
        assert all(q.error is None for q in quote.irans)

    async def test_a_source_with_no_fetcher_is_skipped(
        self, uow: PGUnitOfWork
    ) -> None:
        # the token-gated sources are seeded but have no fetcher at all
        context = _context(_source_context(SourceCode.NAVASAN))

        quote = await _engine(uow)._fetch_all_http(context)

        assert list(quote.irans) == []
        assert list(quote.suppliers) == []
        assert list(quote.globals) == []
        assert list(quote.bubbles) == []

    async def test_each_family_lands_in_its_own_bucket(
        self, uow: PGUnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin(monkeypatch, _BOARD)
        context = _context(
            _source_context(SourceCode.TGJU),
            _source_context(SourceCode.TALALAND, SourceSwitch.SUPPLIER),
            _source_context(SourceCode.GOLD_API, SourceSwitch.GLOBAL_MARKET),
        )

        quote = await _engine(uow)._fetch_all_http(context)

        assert len(quote.irans) == 2
        assert len(quote.suppliers) == 1
        assert len(quote.globals) == 1

    async def test_a_source_in_two_registries_is_fetched_twice(
        self, uow: PGUnitOfWork
    ) -> None:
        # melligold quotes a price and publishes a bubble; picking the
        # registry by market would silently drop one of them
        context = _context(_source_context(SourceCode.MELIGOLD))

        quote = await _engine(uow)._fetch_all_http(context)

        assert len(quote.irans) == 1
        assert len(quote.bubbles) == 1

    async def test_a_failing_source_does_not_sink_the_crawl(
        self, uow: PGUnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin(monkeypatch, {"nothing": "here"})
        context = _context(
            _source_context(SourceCode.TGJU),
            _source_context(SourceCode.GOLD_API, SourceSwitch.GLOBAL_MARKET),
        )

        quote = await _engine(uow)._fetch_all_http(context)

        assert all(q.error is not None for q in quote.irans)
        assert len(quote.globals) == 1

    async def test_an_empty_context_calls_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        quote = await _engine(uow)._fetch_all_http(_context())

        assert list(quote.irans) == []
        assert list(quote.bubbles) == []

    async def test_the_stored_config_reaches_the_fetcher(
        self, uow: PGUnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # the login task refreshes headers_credentials; the crawl only
        # reads it, and both it and the timeout must survive the hand-off
        seen: dict[str, object] = {}

        async def _capture(self: object, client: object) -> httpx.Response:
            seen["timeout"] = getattr(self, "timeout")
            seen["headers"] = getattr(self, "headers_credentials")
            return httpx.Response(
                200,
                json=_BOARD,
                request=httpx.Request("GET", "https://example.test"),
            )

        monkeypatch.setattr(iran_market.TgjuFetcher, "_request", _capture)
        source = _source_context(SourceCode.TGJU)
        source.cfg.timeout = 3
        source.cfg.headers_credentials = {"Cookie": "session=abc"}

        await _engine(uow)._fetch_all_http(_context(source))

        assert seen["timeout"] == 3
        assert seen["headers"] == {"Cookie": "session=abc"}


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestFetchAllHTTPFromTheDatabase:
    async def test_it_crawls_what_fetch_all_db_read(
        self, uow: PGUnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pin(monkeypatch, _BOARD)
        sources = _sources(uow)
        await sources.create(
            _source_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )
        await sources.create(
            _source_data(SourceCode.NAVASAN, SourceSwitch.IRAN_MARKET)
        )
        engine = _engine(uow)

        context = await engine._fetch_all_db()
        quote = await engine._fetch_all_http(context)

        # navasan is seeded but has no fetcher, so only tgju answered
        assert len(quote.irans) == 2
        assert {q.code for q in quote.irans} == {SourceCode.TGJU}
