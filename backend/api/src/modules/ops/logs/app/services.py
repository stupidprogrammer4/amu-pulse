from src.common.bases.schemas import PagerMeta
from src.modules.ops.logs.domain.dtos import LogChartSearch, LogSearch
from src.modules.ops.logs.domain.enums import LogBucket
from src.modules.ops.logs.domain.results import (
    LogChartResult,
    LogSearchResult,
)
from src.modules.ops.logs.domain.schemas import (
    LogChartMeta,
    LogChartOut,
    LogMeta,
    LogOut,
    LogPointOut,
)
from src.modules.ops.logs.domain.types import LogPageType
from src.modules.ops.logs.infra.repository import LogRepository

TRACE_LIMIT = 500


class LogService:
    def __init__(self, repo: LogRepository) -> None:
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
            loggers=page.loggers,
            containers=page.containers,
        )
        return LogSearchResult(data=self._lines(page), meta=meta)

    async def get_chart(
        self, bucket: LogBucket, data: LogChartSearch
    ) -> LogChartResult:
        """
        Desc: Get how much one container wrote over the window its bucket
            size covers, so a reader can see when it was busy and when it
            was failing.
        Args:
            bucket (LogBucket): The bucket width, which picks the window.
            data (LogChartSearch): The container and an optional level.
        Returns:
            return (LogChartResult): The series and its summary, with every
                level and container to filter by.
        """
        chart = await self.repo.get_chart(
            data.container, bucket, data.level
        )
        return LogChartResult(
            data=LogChartOut(
                bucket=bucket,
                points=LogPointOut.from_objs(chart.points),
                min=chart.min,
                max=chart.max,
                mean=chart.mean,
            ),
            meta=LogChartMeta(
                levels=list(chart.levels),
                containers=list(chart.containers),
                buckets=list(LogBucket),
            ),
        )

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
        return [LogOut(**doc.to_dict()) for doc in page.items]
