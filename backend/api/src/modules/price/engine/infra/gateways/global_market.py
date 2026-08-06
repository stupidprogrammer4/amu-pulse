from typing import Sequence

import httpx

from src.modules.price.engine.domain.quotes import (
    ErrorQuote,
    GlobalSourceQuote,
)
from src.modules.price.engine.infra.gateways.base import (
    AbstractFetcher,
    json_path,
)
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.symbols.domain.enums import SymbolCode


class AbstractGlobalFetcher(AbstractFetcher[GlobalSourceQuote]):
    __symbol__: SymbolCode = SymbolCode.XAU_OUNCE

    def _failed(self, error: ErrorQuote) -> Sequence[GlobalSourceQuote]:
        return [
            GlobalSourceQuote.failed(self.__code__, self.__symbol__, error)
        ]


class GoldApiComFetcher(AbstractGlobalFetcher):
    __code__ = SourceCode.GOLD_API
    __url__ = "https://api.gold-api.com/price/XAU"

    def _parse(self, resp: httpx.Response) -> Sequence[GlobalSourceQuote]:
        price = json_path(resp.json(), "price")
        quote = GlobalSourceQuote.from_mid(
            self.__code__, self.__symbol__, price
        )
        return [quote]


class GoldPriceDevFetcher(AbstractGlobalFetcher):
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


GLOBAL_FETCHERS: dict[SourceCode, type[AbstractGlobalFetcher]] = {
    SourceCode.GOLD_API: GoldApiComFetcher,
    SourceCode.GOLDPRICE_DEV: GoldPriceDevFetcher,
}
