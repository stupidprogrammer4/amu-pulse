from typing import TypeVar

from .base import (
    BaseIDModel,
    BaseIDTimestampModel,
    BaseModel,
    BaseTimestampModel,
)

TModel = TypeVar("TModel", bound=BaseModel)
TIDModel = TypeVar("TIDModel", bound=BaseIDModel)
TTimestampModel = TypeVar("TTimestampModel", bound=BaseTimestampModel)
TIDTimestampModel = TypeVar("TIDTimestampModel", bound=BaseIDTimestampModel)
