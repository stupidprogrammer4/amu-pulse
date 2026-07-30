from enum import StrEnum


class QuoteKind(StrEnum):
    # whether a supplier quotes a mazane (per-mesghal) or a per-gram price
    MAZANE = "mazane"
    PER_GRAM = "per_gram"


class SelectionReason(StrEnum):
    # why a reading was left out of the asset's final price
    OUTLIER = "outlier"
    SWITCH_OFF = "switch_off"
