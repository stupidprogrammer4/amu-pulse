from __future__ import annotations

from decimal import Decimal

# gold
# grams of 18-carat gold in one mazane: a mesghal is 4.6083 g, quoted at 17
# carat, so 4.6083 * (0.705 / 0.750). Suppliers quote the mazane; everything
# downstream is per-gram.
MAZANE_FACTOR = Decimal("4.331802")
# grams in a troy ounce, the unit every world feed quotes gold in
TROY_OUNCE_GRAMS = Decimal("31.1034768")

# numbers
INT32_MAX = 2_147_483_647
INT32_MIN = -2_147_483_648
INT64_MAX = 9_223_372_036_854_775_807
INT64_MIN = -9_223_372_036_854_775_808
UINT32_MAX = 4_294_967_295
UINT64_MAX = 18_446_744_073_709_551_615
