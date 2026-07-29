from dataclasses import dataclass
from typing import Sequence

from src.modules.price.sources.domain.enums import ErrorType


@dataclass
class HTTPErrorQuote:
    raw_content: str
    status_code: str
    json: dict[str, str] | None

@dataclass
class ErrorQuote:
    error_type: ErrorType
    message: str
    http_error: HTTPErrorQuote | None

@dataclass
class GlobalSourceQuote:
    ...

@dataclass
class IranSourceQuote:
    ...

@dataclass
class SupplierSourceQuote:
    ...

@dataclass
class SourceQuote:
    irans: Sequence[IranSourceQuote]
    globals: Sequence[GlobalSourceQuote]
    suppliers: Sequence[SupplierSourceQuote]
