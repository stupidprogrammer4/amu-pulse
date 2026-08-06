from enum import StrEnum


class SymbolCode(StrEnum):
    GOLD18_GRAM = "gold18_gram"
    GOLD18_MAZANE = "gold18_mazane"
    XAU_OUNCE = "xau_ounce"
    USD_RIAL = "usd_rial"


class CurrencyType(StrEnum):
    RIAL = "rial"
    USD = "usd"
