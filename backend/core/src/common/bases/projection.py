from abc import ABC, abstractmethod
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel

from src.infra.es.repository import TESRepository
from src.infra.postgres.repository.typing import TPGRepository


class AbstractESProjection(ABC, Generic[TPGRepository, TESRepository]):
    def __init__(self, pg_repo: TPGRepository, es_repo: TESRepository) -> None:
        self.pg_repo = pg_repo
        self.es_repo = es_repo

    @abstractmethod
    async def project(self, id: int) -> bool: ...

    async def unproject(self, id: int) -> bool:
        existing = await self.es_repo.get(str(id))
        if existing is not None:
            await self.es_repo.delete(existing)
        return True


TESProjection = TypeVar("TESProjection", bound=AbstractESProjection)


class AbstractBatchProjection(ABC, Generic[TPGRepository, TESRepository]):
    def __init__(self, pg_repo: TPGRepository, es_repo: TESRepository) -> None:
        self.pg_repo = pg_repo
        self.es_repo = es_repo

    @abstractmethod
    async def batch_project(self, ids: Sequence[int]) -> bool: ...


TBatchProjection = TypeVar("TBatchProjection", bound=AbstractBatchProjection)


TPayload = TypeVar("TPayload", bound=BaseModel)


class AbstractPayloadProjection(ABC, Generic[TESRepository, TPayload]):
    def __init__(self, es_repo: TESRepository) -> None:
        self.es_repo = es_repo

    @abstractmethod
    async def project(self, payload: TPayload) -> bool: ...


TPayloadProjection = TypeVar(
    "TPayloadProjection", bound=AbstractPayloadProjection
)


class AbstractBatchPayloadProjection(ABC, Generic[TESRepository, TPayload]):
    def __init__(self, es_repo: TESRepository) -> None:
        self.es_repo = es_repo

    @abstractmethod
    async def batch_project(self, payload: Sequence[TPayload]) -> bool: ...


TBatchPayloadProjection = TypeVar(
    "TBatchPayloadProjection", bound=AbstractBatchPayloadProjection
)
