from typing import Sequence

import httpx

from src.modules.price.engine.domain.quotes import (
    ErrorQuote,
    SupplierSourceQuote,
)
from src.modules.price.engine.infra.gateways.base import (
    AbstractFetcher,
    json_path,
    user_agent,
)
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.symbols.domain.enums import SymbolCode


class AbstractSupplierFetcher(AbstractFetcher[SupplierSourceQuote]):
    # a supplier dealing in another metal would say so here
    __symbol__: SymbolCode = SymbolCode.GOLD18_MAZANE

    def _failed(self, error: ErrorQuote) -> Sequence[SupplierSourceQuote]:
        return [
            SupplierSourceQuote.failed(self.__code__, self.__symbol__, error)
        ]


class TalalandFetcher(AbstractSupplierFetcher):
    __code__ = SourceCode.TALALAND

    async def _request(self, client: httpx.AsyncClient) -> httpx.Response:
        username = self.headers_credentials.get("username", "")
        token = self.headers_credentials.get("token", "")
        url = (
            f"https://api.talaland.net/api/getPrice/"
            f"{username}/{token}/abshode-rasmi"
        )
        resp = await client.get(url, headers={"User-Agent": user_agent})
        return resp

    def _parse(self, resp: httpx.Response) -> Sequence[SupplierSourceQuote]:
        data = json_path(resp.json(), "result")
        quote = SupplierSourceQuote.from_pair(
            self.__code__,
            self.__symbol__,
            float(data["bidPrice"]) * 10,
            float(data["askPrice"]) * 10,
            is_closed=not data["marketIsOpen"],
        )
        return [quote]


class MirrokniFetcher(AbstractSupplierFetcher):
    __code__ = SourceCode.MIRROKNI
    __url__ = "https://pnlapi.mirrokni.ir/api/Home/ShopkeeperItemsList"
    # the shopkeeper list is grouped; gold sits in group 1, item 28
    group_id = 1
    item_id = 28

    async def _request(self, client: httpx.AsyncClient) -> httpx.Response:
        headers = {"User-Agent": user_agent, **self.headers_credentials}
        resp = await client.post(
            self.__url__, headers=headers, json={"filter": "all"}
        )
        return resp

    def _parse(self, resp: httpx.Response) -> Sequence[SupplierSourceQuote]:
        items = []
        for group in resp.json().get("Data") or []:
            if group["GroupId"] == self.group_id:
                items = group["Items"]
                break
        info = {}
        for item in items:
            if item["Id"] == self.item_id:
                info = item
                break
        buy, sell = info.get("FeeBuy", 0), info.get("FeeSell", 0)
        quote = SupplierSourceQuote.from_pair(
            self.__code__,
            self.__symbol__,
            sell,
            buy,
            is_closed=not (buy and sell),
        )
        return [quote]


SUPPLIER_FETCHERS: dict[SourceCode, type[AbstractSupplierFetcher]] = {
    SourceCode.MIRROKNI: MirrokniFetcher,
    SourceCode.TALALAND: TalalandFetcher,
}
