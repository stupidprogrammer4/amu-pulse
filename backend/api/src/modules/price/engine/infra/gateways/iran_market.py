from typing import Sequence

import httpx

from src.modules.price.engine.domain.quotes import (
    ErrorQuote,
    FeeQuote,
    IranSourceQuote,
)
from src.modules.price.engine.infra.gateways.base import (
    AbstractFetcher,
    json_path,
)
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.symbols.domain.enums import SymbolCode


class AbstractIranFetcher(AbstractFetcher[IranSourceQuote]):
    __symbols__: tuple[SymbolCode, ...] = (SymbolCode.GOLD18_GRAM,)

    def _failed(self, error: ErrorQuote) -> Sequence[IranSourceQuote]:
        return [
            IranSourceQuote.failed(self.__code__, symbol, error)
            for symbol in self.__symbols__
        ]


class TgjuFetcher(AbstractIranFetcher):
    __code__ = SourceCode.TGJU
    __url__ = (
        "https://call4.tgju.org/ajax.json"
        "?rev=pf2MFAghbHqfa4c5jYzDfSq8c8PmqUq4aZatIEutGCv93T8b0rhYJzSfvjI9"
    )
    __symbols__ = (SymbolCode.GOLD18_GRAM, SymbolCode.USD_RIAL)
    gold_sell_key = "tgju_gold_irg18"
    gold_buy_key = "tgju_gold_irg18_buy"
    dollar_key = "price_dollar_rl"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        board = json_path(resp.json(), "current")
        dollar = json_path(board, self.dollar_key, "p")
        quotes = [
            IranSourceQuote.from_buying_selling(
                self.__code__,
                SymbolCode.GOLD18_GRAM,
                json_path(board, self.gold_sell_key, "p"),
                json_path(board, self.gold_buy_key, "p"),
            ),
            IranSourceQuote.from_buying_selling(
                self.__code__, SymbolCode.USD_RIAL, dollar, dollar
            ),
        ]
        return quotes


class WallexFetcher(AbstractIranFetcher):
    __code__ = SourceCode.WALLEX
    __url__ = "https://api.wallex.ir/v1/depth?symbol=USDTTMN"
    __symbols__ = (SymbolCode.USD_RIAL,)
    toman_to_rial = 10

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        book = json_path(resp.json(), "result")
        ask = json_path(book, "ask", 0, "price")
        bid = json_path(book, "bid", 0, "price")
        quote = IranSourceQuote.from_buying_selling(
            self.__code__,
            SymbolCode.USD_RIAL,
            float(ask) * self.toman_to_rial,
            float(bid) * self.toman_to_rial,
        )
        return [quote]


class DigikalaFetcher(AbstractIranFetcher):
    __code__ = SourceCode.DIGIKALA
    __url__ = "https://api.digikala.com/non-inventory/v1/prices/"
    fee = 0.005

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        price = int(json_path(resp.json(), "gold18", "price")) * 1000
        quote = IranSourceQuote.from_price_and_fee(
            self.__code__,
            SymbolCode.GOLD18_GRAM,
            price,
            FeeQuote(sell_rate=self.fee, buy_rate=self.fee),
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
                quote = IranSourceQuote.from_buying_selling(
                    self.__code__,
                    SymbolCode.GOLD18_GRAM,
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
        quote = IranSourceQuote.from_buying_selling(
            self.__code__, SymbolCode.GOLD18_GRAM, price["sell"], price["buy"]
        )
        return [quote]


class MeligoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.MELIGOLD
    __url__ = "https://melligold.com/api/v1/exchange/buy-sell-price/"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        data = json_path(resp.json(), "data")
        quote = IranSourceQuote.from_buying_selling(
            self.__code__,
            SymbolCode.GOLD18_GRAM,
            int(data["price_buy"]) * 10,
            int(data["price_sell"]) * 10,
        )
        return [quote]


class MiligoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.MILIGOLD
    __url__ = "https://milli.gold/api/v1/public/milli-price/detail"
    fee = 0.005

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        price = int(json_path(resp.json(), "data", "price18")) * 1000
        quote = IranSourceQuote.from_price_and_fee(
            self.__code__,
            SymbolCode.GOLD18_GRAM,
            price,
            FeeQuote(sell_rate=self.fee, buy_rate=self.fee),
        )
        return [quote]


class TechnogoldFetcher(AbstractIranFetcher):
    __code__ = SourceCode.TECHNOGOLD
    __url__ = "https://api2.technogold.gold/customer/tradeables/price/"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        results = json_path(resp.json(), "results")
        quote = IranSourceQuote.from_buying_selling(
            self.__code__,
            SymbolCode.GOLD18_GRAM,
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
        price = int(json_path(resp.json(), "result", "price")) * 10
        quote = IranSourceQuote.from_price_and_fee(
            self.__code__,
            SymbolCode.GOLD18_GRAM,
            price,
            FeeQuote(sell_rate=self.fee, buy_rate=self.fee),
        )
        return [quote]


class TalaseaFetcher(AbstractIranFetcher):
    __code__ = SourceCode.TALASEA
    __url__ = "https://api.talasea.ir/api/market/getGoldPrice"

    def _parse(self, resp: httpx.Response) -> Sequence[IranSourceQuote]:
        data = resp.json()
        price = int(json_path(data, "price")) * 10_000
        fee = float(json_path(data, "feeTable", 0, "fee"))
        quote = IranSourceQuote.from_price_and_fee(
            self.__code__,
            SymbolCode.GOLD18_GRAM,
            price,
            FeeQuote(sell_rate=fee, buy_rate=fee),
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
