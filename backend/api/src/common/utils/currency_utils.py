from decimal import Decimal, InvalidOperation

from src.common.constants import MAZANE_FACTOR
from src.common.utils import persian_utils

QuotedAmount = str | int | float | Decimal


def _normalize(value: QuotedAmount) -> str | None:
    text = None
    if isinstance(value, str):
        text = persian_utils.to_english_digits(value)
        text = text.strip().replace(",", "").replace("،", "")
    return text


def _numeric(value: QuotedAmount) -> int | float | Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"non-numeric amount: {value!r}")
    return value


def round_rial(amount: int | float | Decimal) -> int:
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


def to_cent(value: QuotedAmount) -> int:
    cents = round(to_decimal(value) * 100)
    return cents


def to_mazane(per_gram: int) -> int:
    return round_rial(per_gram * MAZANE_FACTOR)


def from_mazane(mazane: int) -> int:
    return round_rial(mazane / MAZANE_FACTOR)


def from_usd(amount: Decimal, usd_rial: int) -> int:
    return round_rial(amount * Decimal(usd_rial))


def with_bubble(intrinsic: int, bubble: int) -> int:
    return round_rial(intrinsic + bubble)
