from typing import Protocol

from src.modules.ops.logs.domain.dtos import LogSearch
from src.modules.ops.logs.domain.results import LogSearchResult
from src.modules.ops.logs.domain.schemas import LogOut


class ILogService(Protocol):
    async def search(self, data: LogSearch) -> LogSearchResult: ...

    async def get_by_request_id(self, request_id: str) -> list[LogOut]: ...
