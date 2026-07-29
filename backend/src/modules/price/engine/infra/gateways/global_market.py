from typing import Sequence

import httpx

from src.modules.price.engine.domain.enums import GlobalSymbol
from src.modules.price.engine.domain.quotes import (
    ErrorQuote,
    GlobalSourceQuote,
)
from src.modules.price.engine.infra.gateways.base import (
    AbstractFetcher,
    json_path,
    user_agent,
)
from src.modules.price.sources.domain.enums import SourceCode


class AbstractGlobalFetcher(AbstractFetcher[GlobalSourceQuote]):
    __symbol__: GlobalSymbol = GlobalSymbol.XAU

    def _failed(self, error: ErrorQuote) -> Sequence[GlobalSourceQuote]:
        return [
            GlobalSourceQuote.failed(self.__code__, self.__symbol__, error)
        ]


# --- XAU spot ---


class GoldApiComFetcher(AbstractGlobalFetcher):
    # verified live: keyless, one mid price per symbol
    __code__ = SourceCode.GOLD_API
    __url__ = "https://api.gold-api.com/price/XAU"

    def _parse(self, resp: httpx.Response) -> Sequence[GlobalSourceQuote]:
        price = json_path(resp.json(), "price")
        quote = GlobalSourceQuote.from_mid(
            self.__code__, self.__symbol__, price
        )
        return [quote]


class GoldPriceDevFetcher(AbstractGlobalFetcher):
    # verified live: keyless, quotes both sides
    __code__ = SourceCode.GOLDPRICE_DEV
    __url__ = "https://api.goldprice.dev/v1/spot/XAU"

    def _parse(self, resp: httpx.Response) -> Sequence[GlobalSourceQuote]:
        data = resp.json()
        quote = GlobalSourceQuote.from_pair(
            self.__code__,
            self.__symbol__,
            json_path(data, "ask"),
            json_path(data, "bid"),
        )
        return [quote]


# --- the USD side of the FX board ---


class FrankfurterFetcher(AbstractGlobalFetcher):
    # verified live: keyless
    __code__ = SourceCode.FRANKFURTER
    __symbol__ = GlobalSymbol.USD
    __url__ = "https://api.frankfurter.dev/v1/latest"
    # the currency the dollar is measured against
    against = "EUR"

    async def _request(self, client: httpx.AsyncClient) -> httpx.Response:
        headers = {"User-Agent": user_agent, **self.headers_credentials}
        params = {"base": "USD", "symbols": self.against}
        resp = await client.get(self.__url__, headers=headers, params=params)
        return resp

    def _parse(self, resp: httpx.Response) -> Sequence[GlobalSourceQuote]:
        rates = json_path(resp.json(), "rates")
        quote = GlobalSourceQuote.from_mid(
            self.__code__, self.__symbol__, json_path(rates, self.against)
        )
        return [quote]


GLOBAL_FETCHERS: dict[SourceCode, type[AbstractGlobalFetcher]] = {
    SourceCode.FRANKFURTER: FrankfurterFetcher,
    SourceCode.GOLD_API: GoldApiComFetcher,
    SourceCode.GOLDPRICE_DEV: GoldPriceDevFetcher,
}
