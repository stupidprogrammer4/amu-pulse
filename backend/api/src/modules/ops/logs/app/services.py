from src.common.bases.schemas import PagerMeta
from src.modules.ops.logs.domain.dtos import LogSearch
from src.modules.ops.logs.domain.results import LogPageType, LogSearchResult
from src.modules.ops.logs.domain.schemas import LogMeta, LogOut
from src.modules.ops.logs.infra.repository import LogRepository

# a request id gathers a handful of lines, never a page of them
TRACE_LIMIT = 500


class LogService:
    def __init__(self, repo: LogRepository) -> None:
        """
        Desc: Build the service with its repository.
        Args:
            repo (LogRepository): Reads the log data stream.
        """
        self.repo = repo

    async def search(self, data: LogSearch) -> LogSearchResult:
        """
        Desc: Get a filtered page of log lines, newest first.
        Args:
            data (LogSearch): Filters, a time span and paging.
        Returns:
            return (LogSearchResult): The page and its meta.
        """
        page = await self.repo.get_page(
            q=data.q,
            levels=data.levels,
            loggers=data.loggers,
            containers=data.containers,
            request_id=data.request_id,
            start=data.from_time,
            end=data.to_time,
            offset=(data.page - 1) * data.per_page,
            limit=data.per_page,
        )
        meta = LogMeta(
            pager=PagerMeta.from_total(
                data.page, data.per_page, page.total_items
            ),
            levels=page.levels,
        )
        return LogSearchResult(data=self._lines(page), meta=meta)

    async def get_by_request_id(self, request_id: str) -> list[LogOut]:
        """
        Desc: Get everything one request or one task execution wrote, oldest
            first, so the trace reads in the order it happened.
        Args:
            request_id (str): The correlation id to gather.
        Returns:
            return (list[LogOut]): The lines that carry it.
        """
        page = await self.repo.get_page(
            request_id=request_id, limit=TRACE_LIMIT
        )
        lines = self._lines(page)
        lines.reverse()
        return lines

    @staticmethod
    def _lines(page: LogPageType) -> list[LogOut]:
        return [LogOut.from_doc(doc) for doc in page.items]
