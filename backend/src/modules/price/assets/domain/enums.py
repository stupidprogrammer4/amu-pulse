from enum import StrEnum


class AssetCode(StrEnum):
    GOLD18 = "gold18"
    XAU = "xau"
    GOLD_MAZANE = "gold_mazane"
    USD = "usd"


class MetalSymbol(StrEnum):
    GOLD = "gold"
    SILVER = "silver"


class AggregationType(StrEnum):
    MEDIAN = "median"
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    FIRST_QUARTILE = "first_quartile"
    THIRD_QUARTILE = "third_quartile"
