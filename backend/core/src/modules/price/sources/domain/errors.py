from typing import TypedDict

from src.modules.price.sources.domain.enums import ErrorType


class SourceErrorInfo(TypedDict, total=False):
    # what the source's `error` column carries after a failed fetch
    kind: ErrorType
    message: str
    status_code: int
    raw_content: str
