from typing import Sequence

import httpx

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.quotes import BubbleQuote, ErrorQuote
from src.modules.price.engine.infra.gateways.base import (
    AbstractFetcher,
    json_path,
)
from src.modules.price.sources.domain.enums import SourceCode


class AbstractBubbleFetcher(AbstractFetcher[BubbleQuote]):
    __assets__: tuple[AssetCode, ...] = (AssetCode.GOLD18,)

    def _failed(self, error: ErrorQuote) -> Sequence[BubbleQuote]:
        return [
            BubbleQuote.failed(self.__code__, asset, error)
            for asset in self.__assets__
        ]


class MeligoldBubbleFetcher(AbstractBubbleFetcher):
    __code__ = SourceCode.MELIGOLD
    __url__ = "https://cms.melligold.com/api/bubble-rates/latest"
    assets_by_key = {"XAU18_BUBBLE": AssetCode.GOLD18}

    async def _request(self, client: httpx.AsyncClient) -> httpx.Response:
        params = {"key[]": list(self.assets_by_key)}
        resp = await client.get(self.__url__, params=params)
        return resp

    def _parse(self, resp: httpx.Response) -> Sequence[BubbleQuote]:
        quotes = []
        for row in json_path(resp.json(), "data"):
            asset = self.assets_by_key.get(str(row.get("key")))
            if asset is None:
                continue
            quotes.append(
                BubbleQuote.from_amount(self.__code__, asset, row["price"])
            )
        if not quotes:
            raise ValueError("no bubble row in response")
        return quotes


BUBBLE_FETCHERS: dict[SourceCode, type[AbstractBubbleFetcher]] = {
    SourceCode.MELIGOLD: MeligoldBubbleFetcher,
}
