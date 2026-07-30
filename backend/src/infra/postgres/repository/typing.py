from typing import TypeVar

from .base import PGIDRepository, PGRepository, PGTimestampIDRepository

TPGRepository = TypeVar("TPGRepository", bound=PGRepository)
TPGIDRepository = TypeVar("TPGIDRepository", bound=PGIDRepository)
TPGTimestampIDRepository = TypeVar(
    "TPGTimestampIDRepository", bound=PGTimestampIDRepository
)
