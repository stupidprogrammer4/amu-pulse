from typing import Sequence

import httpx

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.quotes import ErrorQuote, IranSourceQuote
from src.modules.price.engine.infra.gateways.base import (
    AbstractFetcher,
    json_path,
)
from src.modules.price.sources.domain.enums import SourceCode


class AbstractIranFetcher(AbstractFetcher[IranSourceQuote]):
    # a failed fetch answers per asset, so none silently disappears
    __assets__: tuple[AssetCode, ...] = (AssetCode.GOLD18,)

    def _failed(self, error: ErrorQuote) -> Sequence[IranSourceQuote]:
        return [
            IranSourceQuote.failed(self.__code__, asset, error)
            for asset in self.__assets__
        ]


# --- rate aggregators ---


class TgjuFetcher(AbstractIranFetcher):
    # verified live: keyless
    __code__ = SourceCode.TGJU
    __url__ = (
        "https://call4.tgju.org/ajax.json"
        "?rev=pf2MFAghbHqfa4c5jYzDfSq8c8PmqUq4aZatIEutGCv93T8b0rhYJzSfvjI9"
    )
    __assets__ = (AssetCode.GOLD18, AssetCode.USD)
    # the board keys each row by symbol and prices it under "p"
    gold_sell_key = "tgju_gold_irg18"
    gold_buy_key = "tgju_gold_irg18_buy"
    dollar_key = "price_dollar_rl"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        board = json_path(resp.json(), "current")
        # the dollar comes as one mid price, gold as a two-sided pair
        dollar = json_path(board, self.dollar_key, "p")
        quotes = [
            IranSourceQuote.from_pair(
                self.__code__,
                AssetCode.GOLD18,
                json_path(board, self.gold_sell_key, "p"),
                json_path(board, self.gold_buy_key, "p"),
            ),
            IranSourceQuote.from_pair(
                self.__code__, AssetCode.USD, dollar, dollar
            ),
        ]
        return quotes


class WallexFetcher(AbstractIranFetcher):
    # verified live: keyless
    __code__ = SourceCode.WALLEX
    __url__ = "https://api.wallex.ir/v1/depth?symbol=USDTTMN"
    __assets__ = (AssetCode.USD,)
    # the book quotes Toman; storage is Rial
    toman_to_rial = 10

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        book = json_path(resp.json(), "result")
        ask = json_path(book, "ask", 0, "price")
        bid = json_path(book, "bid", 0, "price")
        quote = IranSourceQuote.from_pair(
            self.__code__,
            AssetCode.USD,
            float(ask) * self.toman_to_rial,
            float(bid) * self.toman_to_rial,
        )
        return [quote]


# --- online gold shops: watched, not bought from ---


class DigikalaFetcher(AbstractIranFetcher):
    __code__ = SourceCode.DIGIKALA
    __url__ = "https://api.digikala.com/non-inventory/v1/prices/"
    fee = 0.005

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        price = int(json_path(resp.json(), "gold18", "price")) * 1000
        quote = IranSourceQuote.from_pair(
            self.__code__,
            AssetCode.GOLD18,
            round(price * (1 - self.fee)),
            round(price * (1 + self.fee)),
        )
        return [quote]


class TalineFetcher(AbstractIranFetcher):
    __code__ = SourceCode.TALINE
    __url__ = "https://price.tlyn.ir/api/v1/price"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        quote = None
        for row in json_path(resp.json(), "prices"):
            if row["symbol"] == "GOLD18":
                price = row["price"]
                quote = IranSourceQuote.from_pair(
                    self.__code__,
                    AssetCode.GOLD18,
                    float(price["buy"]) * 10_100,
                    float(price["sell"]) * 10_000,
                )
                break
        if quote is None:
            raise ValueError("GOLD18 price not found")
        return [quote]


class GoldikaFetcher(AbstractIranFetcher):
    __code__ = SourceCode.GOLDIKA
    __url__ = "https://api.goldika.ir/api/public/price"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        price = json_path(resp.json(), "data", "price")
        quote = IranSourceQuote.from_pair(
            self.__code__, AssetCode.GOLD18, price["sell"], price["buy"]
        )
        return [quote]


class MeligoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.MELIGOLD
    __url__ = "https://melligold.com/api/v1/exchange/buy-sell-price/"
    fee = 0.005

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        data = json_path(resp.json(), "data")
        buy = round(int(data["price_buy"]) * 10 * (1 + self.fee))
        sell = round(int(data["price_sell"]) * 10 * (1 - self.fee))
        quote = IranSourceQuote.from_pair(
            self.__code__, AssetCode.GOLD18, sell, buy
        )
        return [quote]


class MiligoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.MILIGOLD
    __url__ = "https://milli.gold/api/v1/public/milli-price/detail"
    fee = 0.005

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        price = int(json_path(resp.json(), "data", "price18")) * 1000
        quote = IranSourceQuote.from_pair(
            self.__code__,
            AssetCode.GOLD18,
            round(price * (1 - self.fee)),
            round(price * (1 + self.fee)),
        )
        return [quote]


class TechnogoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.TECHNOGOLD
    __url__ = "https://api2.technogold.gold/customer/tradeables/price/"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        results = json_path(resp.json(), "results")
        quote = IranSourceQuote.from_pair(
            self.__code__,
            AssetCode.GOLD18,
            int(results["sell_price"]) * 10,
            int(results["buy_price"]) * 10,
        )
        return [quote]


class WallgoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.WALLGOLD
    __url__ = (
        "https://api.wallgold.ir/api/v1/price?side=buy&symbol=GLD_18C_750TMN"
    )
    fee = 0.0005

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        price = int(json_path(resp.json(), "result", "price"))
        buy = round(price * (1 + self.fee) * 10)
        sell = round(price * (1 - self.fee) * 10)
        quote = IranSourceQuote.from_pair(
            self.__code__, AssetCode.GOLD18, sell, buy
        )
        return [quote]


class TalaseaFetcher(AbstractIranFetcher):
    __code__ = SourceCode.TALASEA
    __url__ = "https://api.talasea.ir/api/market/getGoldPrice"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        data = resp.json()
        price = int(json_path(data, "price")) * 10_000
        fee = float(json_path(data, "feeTable", 0, "fee"))
        quote = IranSourceQuote.from_pair(
            self.__code__,
            AssetCode.GOLD18,
            round(price * (1 - fee)),
            round(price * (1 + fee)),
        )
        return [quote]


IRAN_FETCHERS: dict[SourceCode, type[AbstractIranFetcher]] = {
    SourceCode.DIGIKALA: DigikalaFetcher,
    SourceCode.GOLDIKA: GoldikaFetcher,
    SourceCode.MELIGOLD: MeligoldFetcher,
    SourceCode.MILIGOLD: MiligoldFetcher,
    SourceCode.TALASEA: TalaseaFetcher,
    SourceCode.TALINE: TalineFetcher,
    SourceCode.TECHNOGOLD: TechnogoldFetcher,
    SourceCode.TGJU: TgjuFetcher,
    SourceCode.WALLEX: WallexFetcher,
    SourceCode.WALLGOLD: WallgoldFetcher,
}
