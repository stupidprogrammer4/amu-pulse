from typing import Protocol

from src.modules.ops.logs.domain.dtos import LogChartSearch, LogSearch
from src.modules.ops.logs.domain.enums import LogBucket
from src.modules.ops.logs.domain.results import (
    LogChartResult,
    LogSearchResult,
)
from src.modules.ops.logs.domain.schemas import LogOut


class ILogService(Protocol):
    async def search(self, data: LogSearch) -> LogSearchResult: ...

    async def get_chart(
        self, bucket: LogBucket, data: LogChartSearch
    ) -> LogChartResult: ...

    async def get_by_request_id(self, request_id: str) -> list[LogOut]: ...
