from enum import StrEnum


class SourceSwitch(StrEnum):
    SUPPLIER = "supplier"
    GLOBAL_MARKET = "global_market"
    IRAN_MARKET = "iran_market"


class ErrorType(StrEnum):
    LOGICAL_ERROR = "logical"
    HTTP_ERROR = "http"


class SourceCode(StrEnum):
    # --- supplier: the Iranian gold shops we quote against ---
    DIGIKALA = "digikala"
    GOLDIKA = "goldika"
    MELIGOLD = "meligold"
    MILIGOLD = "miligold"
    MIRROKNI = "mirrokni"
    NOGHRESEA = "noghresea"
    TALALAND = "talaland"
    TALASEA = "talasea"
    TALINE = "taline"
    TECHNOGOLD = "technogold"
    WALLGOLD = "wallgold"

    # --- iran_market: rial-denominated gold and USD quotes ---
    ALANCHAND = "alanchand"
    NAVASAN = "navasan"
    NERKH_API = "nerkh_api"
    TGJU = "tgju"

    # --- global_market: XAU spot ---
    COMMODITY_PRICE_API = "commodity_price_api"
    EODHD = "eodhd"
    GOLD_API = "gold_api"
    GOLDAPI_IO = "goldapi_io"
    GOLDAPI_NET = "goldapi_net"
    GOLDPRICE_DEV = "goldprice_dev"
    METALPRICE_API = "metalprice_api"
    METALS_API = "metals_api"
    TWELVE_DATA = "twelve_data"
    UNIRATE_API = "unirate_api"
    XAUS = "xaus"

    # --- global_market: USD and the rest of the FX board ---
    CURRENCY_LAYER = "currency_layer"
    EXCHANGERATE_API = "exchangerate_api"
    EXCHANGERATES_API = "exchangerates_api"
    FIXER = "fixer"
    FRANKFURTER = "frankfurter"
    FREE_CURRENCY_API = "free_currency_api"
    OPEN_EXCHANGE_RATES = "open_exchange_rates"
