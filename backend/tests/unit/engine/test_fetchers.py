from decimal import Decimal
from typing import Any, Sequence

import httpx
import pytest

from src.common.utils.currency_utils import round_rial
from src.modules.price.engine.domain.enums import QuoteKind
from src.modules.price.engine.infra.gateways.base import AbstractFetcher
from src.modules.price.engine.infra.gateways.global_market import (
    GLOBAL_FETCHERS,
    GoldApiComFetcher,
    GoldPriceDevFetcher,
)
from src.modules.price.engine.infra.gateways.iran_market import (
    IRAN_FETCHERS,
    DigikalaFetcher,
    GoldikaFetcher,
    TgjuFetcher,
    WallexFetcher,
)
from src.modules.price.engine.infra.gateways.supplier import (
    SUPPLIER_FETCHERS,
    MirrokniFetcher,
    TalalandFetcher,
)
from src.modules.price.sources.domain.enums import (
    ErrorType,
    SourceCode,
    SourceSwitch,
)
from src.modules.price.symbols.domain.enums import SymbolCode
from src.seeders.sources import SOURCES


def _respond(fetcher: AbstractFetcher[Any], payload: Any, status: int = 200):
    """
    Desc: Pin a fetcher's HTTP call to a canned response.
    Args:
        fetcher (AbstractFetcher[Any]): The fetcher to pin.
        payload (Any): The JSON body to answer with.
        status (int): The status code to answer with.
    """

    async def _request(client: httpx.AsyncClient) -> httpx.Response:
        return httpx.Response(
            status,
            json=payload,
            request=httpx.Request("GET", "https://example.test"),
        )

    fetcher._request = _request  # type: ignore[method-assign]


async def _fetch(fetcher: AbstractFetcher[Any], payload: Any) -> Sequence[Any]:
    """
    Desc: Run a fetcher against a canned body and hand back its quotes.
    Args:
        fetcher (AbstractFetcher[Any]): The fetcher to run.
        payload (Any): The JSON body to answer with.
    Returns:
        return (Sequence[Any]): The quotes it parsed.
    """
    _respond(fetcher, payload)
    quotes = await fetcher.fetch()
    return quotes


def _tgju_board() -> dict[str, Any]:
    """
    Desc: Build a TGJU board carrying its gold pair and dollar row.
    Returns:
        return (dict[str, Any]): The response body.
    """
    return {
        "current": {
            "tgju_gold_irg18": {"p": "197631000"},
            "tgju_gold_irg18_buy": {"p": "195925000"},
            # the board prints the dollar with thousands separators
            "price_dollar_rl": {"p": "1,931,900"},
        }
    }


class TestIranFetchers:
    async def test_tgju_reads_the_18k_gold_pair(self) -> None:
        quotes = await _fetch(TgjuFetcher(), _tgju_board())

        gold = next(q for q in quotes if q.symbol == SymbolCode.GOLD18_GRAM)
        assert gold.sell_price_rial == 197_631_000
        assert gold.buy_price_rial == 195_925_000
        assert gold.error is None

    async def test_tgju_reads_the_rial_dollar(self) -> None:
        quotes = await _fetch(TgjuFetcher(), _tgju_board())

        dollar = next(q for q in quotes if q.symbol == SymbolCode.USD_RIAL)
        # separators are stripped, not treated as text
        assert dollar.sell_price_rial == 1_931_900
        assert dollar.buy_price_rial == 1_931_900

    async def test_wallex_reads_the_best_bid_and_ask_in_rial(self) -> None:
        payload = {
            "result": {
                "ask": [{"price": 193_403}, {"price": 193_420}],
                "bid": [{"price": 193_113}, {"price": 193_100}],
            }
        }

        quotes = await _fetch(WallexFetcher(), payload)

        assert quotes[0].symbol == SymbolCode.USD_RIAL
        # the book quotes Toman; storage is Rial
        assert quotes[0].sell_price_rial == 1_934_030
        assert quotes[0].buy_price_rial == 1_931_130

    async def test_digikala_spreads_its_mid_price_by_the_fee(self) -> None:
        quotes = await _fetch(
            DigikalaFetcher(), {"gold18": {"price": 100_000}}
        )

        mid = 100_000 * 1000
        assert quotes[0].sell_price_rial == round_rial(mid * 1.005)
        assert quotes[0].buy_price_rial == round_rial(mid * 0.995)

    async def test_goldika_reads_its_nested_pair(self) -> None:
        payload = {
            "data": {"price": {"sell": 186_000_000, "buy": 185_000_000}}
        }

        quotes = await _fetch(GoldikaFetcher(), payload)

        assert quotes[0].sell_price_rial == 186_000_000
        assert quotes[0].buy_price_rial == 185_000_000

    async def test_a_gold_only_source_does_not_claim_a_dollar(self) -> None:
        quotes = await _fetch(
            DigikalaFetcher(), {"gold18": {"price": 100_000}}
        )

        assert {q.symbol for q in quotes} == {SymbolCode.GOLD18_GRAM}

    async def test_the_dollar_has_at_least_one_keyless_source(self) -> None:
        # every rate aggregator that quotes the dollar sits behind a token,
        # so losing these two would leave USD with nothing at all
        priced = {
            code
            for code, fetcher in IRAN_FETCHERS.items()
            if SymbolCode.USD_RIAL in fetcher.__symbols__
        }
        assert priced == {SourceCode.TGJU, SourceCode.WALLEX}


class TestSupplierFetchers:
    async def test_talaland_reads_a_mazane_pair(self) -> None:
        payload = {
            "result": {
                "bidPrice": 81_000_000,
                "askPrice": 81_200_000,
                "marketIsOpen": True,
            }
        }

        quotes = await _fetch(TalalandFetcher(), payload)

        assert quotes[0].kind == QuoteKind.MAZANE
        assert quotes[0].selling_mazane == 812_000_000
        assert quotes[0].buying_mazane == 810_000_000
        assert quotes[0].is_closed is False

    async def test_talaland_reports_a_closed_market(self) -> None:
        payload = {
            "result": {
                "bidPrice": 1,
                "askPrice": 2,
                "marketIsOpen": False,
            }
        }

        quotes = await _fetch(TalalandFetcher(), payload)

        assert quotes[0].is_closed is True

    async def test_mirrokni_picks_its_gold_item(self) -> None:
        payload = {
            "Data": [
                {
                    "GroupId": 2,
                    "Items": [{"Id": 28, "FeeBuy": 1, "FeeSell": 2}],
                },
                {
                    "GroupId": 1,
                    "Items": [
                        {"Id": 9, "FeeBuy": 5, "FeeSell": 6},
                        {
                            "Id": 28,
                            "FeeBuy": 810_000_000,
                            "FeeSell": 812_000_000,
                        },
                    ],
                },
            ]
        }

        quotes = await _fetch(MirrokniFetcher(), payload)

        assert quotes[0].selling_mazane == 812_000_000
        assert quotes[0].buying_mazane == 810_000_000

    async def test_mirrokni_treats_a_zero_price_as_closed(self) -> None:
        payload = {
            "Data": [
                {
                    "GroupId": 1,
                    "Items": [{"Id": 28, "FeeBuy": 0, "FeeSell": 0}],
                }
            ]
        }

        quotes = await _fetch(MirrokniFetcher(), payload)

        assert quotes[0].is_closed is True


class TestGlobalFetchers:
    async def test_gold_api_reads_a_mid_price(self) -> None:
        quotes = await _fetch(
            GoldApiComFetcher(), {"price": 4039.600098, "symbol": "XAU"}
        )

        assert quotes[0].symbol == SymbolCode.XAU_OUNCE
        assert quotes[0].selling == Decimal("4039.600098")
        assert quotes[0].selling == quotes[0].buying

    async def test_goldprice_dev_reads_bid_and_ask(self) -> None:
        payload = {"price": "4038.41", "bid": "4037.47", "ask": "4039.34"}

        quotes = await _fetch(GoldPriceDevFetcher(), payload)

        assert quotes[0].selling == Decimal("4039.34")
        assert quotes[0].buying == Decimal("4037.47")


class TestFetchNeverRaises:
    async def test_an_http_status_becomes_an_http_error_quote(self) -> None:
        fetcher = TgjuFetcher()
        _respond(fetcher, {"detail": "nope"}, status=503)

        quotes = await fetcher.fetch()

        assert quotes[0].error is not None
        assert quotes[0].error.error_type == ErrorType.HTTP_ERROR
        assert quotes[0].error.http_error is not None
        assert quotes[0].error.http_error.status_code == "503"

    async def test_a_missing_field_becomes_a_logical_error_quote(self) -> None:
        quotes = await _fetch(TgjuFetcher(), {"nothing": "here"})

        assert quotes[0].error is not None
        assert quotes[0].error.error_type == ErrorType.LOGICAL_ERROR
        assert "current" in quotes[0].error.message

    async def test_a_multi_asset_source_fails_every_asset(self) -> None:
        # a dropped asset would silently vanish from the aggregate
        quotes = await _fetch(TgjuFetcher(), {"junk": 1})

        assert {q.symbol for q in quotes} == {
            SymbolCode.GOLD18_GRAM,
            SymbolCode.USD_RIAL,
        }
        assert all(q.error is not None for q in quotes)

    async def test_a_failed_fetch_is_zero_priced(self) -> None:
        quotes = await _fetch(GoldApiComFetcher(), {"junk": 1})

        assert quotes[0].selling == Decimal(0)
        assert quotes[0].buying == Decimal(0)

    async def test_a_transport_failure_is_caught(self) -> None:
        fetcher = TgjuFetcher()

        async def _boom(client: httpx.AsyncClient) -> httpx.Response:
            raise httpx.ConnectTimeout("timed out")

        fetcher._request = _boom  # type: ignore[method-assign]

        quotes = await fetcher.fetch()

        assert quotes[0].error is not None
        assert quotes[0].error.error_type == ErrorType.HTTP_ERROR


class TestRegistries:
    def test_each_registry_matches_its_market(self) -> None:
        switch_by_code = {s.code: s.switch for s in SOURCES}
        for code in SUPPLIER_FETCHERS:
            assert switch_by_code[code] == SourceSwitch.SUPPLIER
        for code in IRAN_FETCHERS:
            assert switch_by_code[code] == SourceSwitch.IRAN_MARKET
        for code in GLOBAL_FETCHERS:
            assert switch_by_code[code] == SourceSwitch.GLOBAL_MARKET

    def test_only_the_two_wholesalers_are_suppliers(self) -> None:
        assert set(SUPPLIER_FETCHERS) == {
            SourceCode.MIRROKNI,
            SourceCode.TALALAND,
        }

    def test_no_source_code_has_two_fetchers(self) -> None:
        codes = (
            list(SUPPLIER_FETCHERS)
            + list(IRAN_FETCHERS)
            + list(GLOBAL_FETCHERS)
        )
        assert len(codes) == len(set(codes))

    def test_only_the_known_sources_lack_a_fetcher(self) -> None:
        # every source that needs an api key is seeded but not fetched; the
        # two wholesalers are the only credentialed exception. Pin the list
        # so a newly added source without a fetcher fails here.
        expected = {
            # quotes silver, which SymbolCode does not model yet
            SourceCode.NOGHRESEA,
            # quotes the dollar against the euro, which prices nothing here
            SourceCode.FRANKFURTER,
            # rial rates behind a token
            SourceCode.ALANCHAND,
            SourceCode.NAVASAN,
            SourceCode.NERKH_API,
            # XAU spot behind an api key
            SourceCode.COMMODITY_PRICE_API,
            SourceCode.EODHD,
            SourceCode.GOLDAPI_IO,
            SourceCode.GOLDAPI_NET,
            SourceCode.METALPRICE_API,
            SourceCode.METALS_API,
            SourceCode.TWELVE_DATA,
            SourceCode.UNIRATE_API,
            SourceCode.XAUS,
            # FX behind an api key
            SourceCode.CURRENCY_LAYER,
            SourceCode.EXCHANGERATE_API,
            SourceCode.EXCHANGERATES_API,
            SourceCode.FIXER,
            SourceCode.FREE_CURRENCY_API,
            SourceCode.OPEN_EXCHANGE_RATES,
        }
        covered = (
            set(SUPPLIER_FETCHERS) | set(IRAN_FETCHERS) | set(GLOBAL_FETCHERS)
        )
        assert {s.code for s in SOURCES} - covered == expected

    def test_only_the_wholesalers_need_credentials(self) -> None:
        # every other fetcher must work with no auth configured at all
        keyless = set(IRAN_FETCHERS) | set(GLOBAL_FETCHERS)
        assert not keyless & set(SUPPLIER_FETCHERS)
        for fetcher in list(IRAN_FETCHERS.values()) + list(
            GLOBAL_FETCHERS.values()
        ):
            built = fetcher()
            assert built.headers_credentials == {}

    @pytest.mark.parametrize(
        "registry", [SUPPLIER_FETCHERS, IRAN_FETCHERS, GLOBAL_FETCHERS]
    )
    def test_a_fetcher_is_registered_under_its_own_code(
        self, registry: dict[SourceCode, type[AbstractFetcher[Any]]]
    ) -> None:
        for code, fetcher in registry.items():
            assert fetcher.__code__ == code
