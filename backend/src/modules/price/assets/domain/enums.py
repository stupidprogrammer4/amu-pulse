from enum import StrEnum


class AssetCode(StrEnum):
    GOLD18 = "gold18"
    USD = "usd"


class AggregationType(StrEnum):
    MEDIAN = "median"
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    FIRST_QUARTILE = "first_quartile"
    THIRD_QUARTILE = "third_quartile"
