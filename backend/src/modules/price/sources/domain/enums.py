# enums for the source module
from enum import StrEnum


class SourceSwitch(StrEnum):
    SUPPLIER = "supplier"
    GLOBAL_MARKET = "global_market"
    IRAN_MARKET = "iran_market"

class SourceCode(StrEnum):
    ...

class ErrorType:
    LOGICAL_ERROR = "logical"
    HTTP_ERROR = "http"
