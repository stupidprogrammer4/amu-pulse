from typing import Any, Sequence

import httpx

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.infra.gateways.base import AbstractFetcher
from src.modules.price.engine.infra.gateways.bubble import (
    BUBBLE_FETCHERS,
    MeligoldBubbleFetcher,
)
from src.modules.price.sources.domain.enums import ErrorType, SourceCode
from src.seeders.sources import SOURCES


async def _fetch(
    fetcher: AbstractFetcher[Any], payload: Any, status: int = 200
) -> Sequence[Any]:

    async def _request(client: httpx.AsyncClient) -> httpx.Response:
        return httpx.Response(
            status,
            json=payload,
            request=httpx.Request("GET", "https://example.test"),
        )

    fetcher._request = _request  # type: ignore[method-assign]
    quotes = await fetcher.fetch()
    return quotes


def _row(key: str, price: str) -> dict[str, Any]:
    return {"key": key, "title": "حباب", "price": price, "change": "0"}


class TestMeligoldBubbleFetcher:
    async def test_it_reads_the_18k_premium(self) -> None:
        payload = {"data": [_row("XAU18_BUBBLE", "3241000")]}

        quotes = await _fetch(MeligoldBubbleFetcher(), payload)

        assert len(quotes) == 1
        assert quotes[0].asset == AssetCode.GOLD18
        assert quotes[0].amount == 3_241_000
        assert quotes[0].error is None

    async def test_a_negative_premium_is_kept(self) -> None:
        payload = {"data": [_row("XAU18_BUBBLE", "-2137540")]}

        quotes = await _fetch(MeligoldBubbleFetcher(), payload)

        assert quotes[0].amount == -2_137_540

    async def test_rows_for_unmodelled_assets_are_skipped(self) -> None:
        payload = {
            "data": [
                _row("524695", "38950000"),
                _row("XAU24_BUBBLE", "-1053627"),
                _row("XAU18_BUBBLE", "-2137540"),
            ]
        }

        quotes = await _fetch(MeligoldBubbleFetcher(), payload)

        assert [q.amount for q in quotes] == [-2_137_540]

    async def test_a_body_without_our_row_is_an_error(self) -> None:
        payload = {"data": [_row("XAU24_BUBBLE", "-1053627")]}

        quotes = await _fetch(MeligoldBubbleFetcher(), payload)

        assert quotes[0].error is not None
        assert quotes[0].error.error_type == ErrorType.LOGICAL_ERROR

    async def test_a_failed_fetch_carries_a_zero_premium(self) -> None:
        quotes = await _fetch(
            MeligoldBubbleFetcher(), {"detail": "nope"}, status=502
        )

        assert quotes[0].amount == 0
        assert quotes[0].error is not None
        assert quotes[0].error.error_type == ErrorType.HTTP_ERROR

    def test_the_bubble_source_is_seeded(self) -> None:
        assert SourceCode.MELIGOLD in {s.code for s in SOURCES}

    def test_a_fetcher_is_registered_under_its_own_code(self) -> None:
        for code, fetcher in BUBBLE_FETCHERS.items():
            assert fetcher.__code__ == code

    def test_it_needs_no_credentials(self) -> None:
        built = MeligoldBubbleFetcher()

        assert built.headers_credentials == {}
