from collections.abc import Sequence
from datetime import datetime
from typing import Any

from elasticsearch import NotFoundError
from elasticsearch.dsl import AsyncSearch

from src.infra.es.repository import ESRepository
from src.modules.ops.logs.domain.documents import LogDocument
from src.modules.ops.logs.domain.results import (
    LogPageType,
)

MAX_WINDOW = 10_000


class LogRepository(ESRepository[LogDocument]):
    def _filtered(
        self,
        *,
        q: str | None = None,
        levels: Sequence[str] | None = None,
        loggers: Sequence[str] | None = None,
        containers: Sequence[str] | None = None,
        request_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> AsyncSearch[LogDocument]:
        """
        Desc: Build the search every read shares, so a chart is drawn over
            exactly the lines the same filters would have listed.
        Args:
            q (str | None): Free text over the message.
            levels (Sequence[str] | None): Keep only these levels.
            loggers (Sequence[str] | None): Keep only these loggers' lines.
            containers (Sequence[str] | None): Keep only these containers'.
            request_id (str | None): Keep one request or task execution.
            start (datetime | None): Oldest line to keep.
            end (datetime | None): Newest line to keep.
        Returns:
            return (AsyncSearch[LogDocument]): The filtered search.
        """
        search = self.search()

        for name, values in (
            ("log.level", levels),
            ("log.logger", loggers),
            ("container.name", containers),
        ):
            if values:
                search = search.filter("terms", **{name: list(values)})

        if request_id:
            search = search.filter("term", request_id=request_id)

        span: dict[str, Any] = {}
        if start:
            span["gte"] = start
        if end:
            span["lte"] = end
        if span:
            search = search.filter("range", **{"@timestamp": span})

        if q:
            search = search.query("match_phrase", message=q)

        return search

    async def get_5m_chart(
        self,
        container_name: str,
    ):
        # TODO: last 24 chart in 5m buckets
        ...

    async def get_hourly_chart(
        self,
        container_name: str,
    ):
        # TODO: last week chart in hourly bucket
        ...

    async def get_

    async def get_page(
        self,
        *,
        q: str | None = None,
        levels: Sequence[str] | None = None,
        loggers: Sequence[str] | None = None,
        containers: Sequence[str] | None = None,
        request_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> LogPageType:
        """
        Desc: Page through the log stream, newest first, with a count of
            each level over the whole match.
        Args:
            q (str | None): Free text over the message.
            levels (Sequence[str] | None): Keep only these levels.
            loggers (Sequence[str] | None): Keep only these loggers' lines.
            containers (Sequence[str] | None): Keep only these containers'.
            request_id (str | None): Keep one request or task execution.
            start (datetime | None): Oldest line to keep.
            end (datetime | None): Newest line to keep.
            offset (int): Lines to skip.
            limit (int): Page size.
        Returns:
            return (LogPageType): The page, the total and the level counts.
        """
        search = self._filtered(
            q=q,
            levels=levels,
            loggers=loggers,
            containers=containers,
            request_id=request_id,
            start=start,
            end=end,
        )

        search.aggs.bucket("levels", "terms", field="log.level", size=10)

        start_at = min(offset, MAX_WINDOW - limit)
        search = search.sort("-@timestamp").extra(track_total_hits=True)

        try:
            response = await search[start_at : start_at + limit].execute()
        except NotFoundError:
            return LogPageType(items=[], total_items=0)

        level_counts = {
            bucket.key: bucket.doc_count
            for bucket in response.aggregations.levels.buckets
        }
        total = response.to_dict()["hits"]["total"]["value"]
        return LogPageType(
            items=list(response.hits),
            total_items=total,
            levels=level_counts,
        )
