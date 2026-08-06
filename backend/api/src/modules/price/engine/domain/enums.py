from enum import StrEnum


class QuoteKind(StrEnum):
    MAZANE = "mazane"
    PER_GRAM = "per_gram"
    OUNCE = "ounce"


class SelectionReason(StrEnum):
    OUTLIER = "outlier"
    SWITCH_OFF = "switch_off"
