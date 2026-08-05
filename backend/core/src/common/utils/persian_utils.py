from __future__ import annotations

from datetime import datetime, tzinfo
from decimal import Decimal

from persiantools import characters, digits
from persiantools.jdatetime import JalaliDateTime

from src.common.utils.date_utils import from_db

THOUSANDS_SEP = "،"
DECIMAL_SEP = "٫"  # U+066B ARABIC DECIMAL SEPARATOR
RIAL_UNIT = "ریال"
TOMAN_UNIT = "تومان"

DEFAULT_DATETIME_FORMAT = "%A %d %B %Y - %H:%M"
DEFAULT_DATE_FORMAT = "%d %B %Y"

Number = int | float | Decimal


def to_persian_digits(value: str | int) -> str:
    return digits.ar_to_fa(digits.en_to_fa(str(value)))


def to_english_digits(value: str) -> str:
    return digits.fa_to_en(digits.ar_to_fa(value))


def normalize_persian(text: str) -> str:
    return to_persian_digits(characters.ar_to_fa(text))


def _group(value: Number) -> str:
    dec = Decimal(str(value))
    negative = dec < 0
    dec = -dec if negative else dec
    int_part = int(dec)
    grouped = f"{int_part:,}".replace(",", THOUSANDS_SEP)

    exponent = dec.as_tuple().exponent
    if isinstance(exponent, int) and exponent < 0:
        frac = f"{dec - int_part:.{-exponent}f}"[2:].rstrip("0")
        if frac:
            grouped = f"{grouped}{DECIMAL_SEP}{frac}"

    return f"-{grouped}" if negative else grouped


def format_number(value: Number, *, persian_digits: bool = True) -> str:
    out = _group(value)
    return to_persian_digits(out) if persian_digits else out


def format_rial(
    amount: Number, *, with_unit: bool = True, persian_digits: bool = True
) -> str:
    text = format_number(amount, persian_digits=persian_digits)
    return f"{text} {RIAL_UNIT}" if with_unit else text


def format_toman(
    rial_amount: int, *, with_unit: bool = True, persian_digits: bool = True
) -> str:
    toman, remainder = divmod(rial_amount, 10)
    value: Number = Decimal(toman) + (
        Decimal(remainder) / 10 if remainder else 0
    )
    text = format_number(value, persian_digits=persian_digits)
    return f"{text} {TOMAN_UNIT}" if with_unit else text


def _to_jalali(dt: datetime, tz: str | tzinfo) -> JalaliDateTime:
    # from_db: naive treated as UTC (DB convention), then shifted into app tz.
    return JalaliDateTime(from_db(dt, tz))


def format_jalali_datetime(
    dt: datetime, tz: str | tzinfo, fmt: str = DEFAULT_DATETIME_FORMAT
) -> str:
    return _to_jalali(dt, tz).strftime(fmt, locale="fa")


def format_jalali_date(
    dt: datetime, tz: str | tzinfo, fmt: str = DEFAULT_DATE_FORMAT
) -> str:
    return _to_jalali(dt, tz).strftime(fmt, locale="fa")
