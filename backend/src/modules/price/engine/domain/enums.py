from enum import StrEnum


class QuoteKind(StrEnum):
    # whether a supplier quotes a mazane (per-mesghal) or a per-gram price
    MAZANE = "mazane"
    PER_GRAM = "per_gram"


class ComputationKind(StrEnum):
    # which arithmetic produced a price, and so which working it carries
    SUPPLIER = "supplier"
    GLOBAL = "global"


class GlobalSymbol(StrEnum):
    # what a global source is quoting, priced in USD
    XAU = "xau"
    USD = "usd"
