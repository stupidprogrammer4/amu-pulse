from decimal import Decimal, InvalidOperation

from src.common.constants import MAZANE_FACTOR
from src.common.utils import persian_utils

# what a decoded price field is allowed to be. A source may hand back a
# string ("1,931,900"), an int, a float or a Decimal — anything else is a
# malformed body, not an amount.
QuotedAmount = str | int | float | Decimal


def _normalize(value: QuotedAmount) -> str | None:
    text = None
    if isinstance(value, str):
        text = persian_utils.to_english_digits(value)
        text = text.strip().replace(",", "").replace("،", "")
    return text


def _numeric(value: QuotedAmount) -> int | float | Decimal:
    # bool passes an int check, and a source reporting True is a bug
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"non-numeric amount: {value!r}")
    return value


def round_rial(amount: int | float | Decimal) -> int:
    # a rial price always ends in a zero; the toman is the unit people read
    rial = round(amount / 10) * 10
    return rial


def to_rial(value: QuotedAmount) -> int:
    number: int | float | Decimal
    text = _normalize(value)
    if text is None:
        number = _numeric(value)
    else:
        try:
            number = float(text)
        except ValueError:
            raise ValueError(f"non-numeric amount: {value!r}") from None
    rial = round(number)
    return rial


def to_decimal(value: QuotedAmount) -> Decimal:
    text = _normalize(value)
    if text is None:
        text = str(_numeric(value))
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"non-numeric amount: {value!r}") from None
    return number


def to_mazane(per_gram: int) -> int:
    return round_rial(per_gram * MAZANE_FACTOR)


def from_mazane(mazane: int) -> int:
    return round_rial(mazane / MAZANE_FACTOR)


def from_usd(amount: Decimal, usd_rial: int) -> int:
    return round_rial(amount * Decimal(usd_rial))


def with_bubble(intrinsic: int, bubble: int) -> int:
    return round_rial(intrinsic + bubble)
