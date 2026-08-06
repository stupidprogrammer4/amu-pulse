from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from elasticsearch import NotFoundError
from elasticsearch.dsl import AsyncSearch, Q

from src.common.utils import date_utils
from src.infra.es.repository import ESRepository
from src.modules.ops.logs.domain.documents import LogDocument
from src.modules.ops.logs.domain.enums import LogBucket
from src.modules.ops.logs.domain.types import (
    LogChartType,
    LogPageType,
    PointType,
)

MAX_WINDOW = 10_000
MAX_FACET = 50


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

    async def get_chart(
        self,
        container_name: str,
        bucket: LogBucket,
        level: str | None = None,
    ) -> LogChartType:
        """
        Desc: Count one container's lines per bucket over the window that
            bucket size covers, with every level the window holds beside
            them so a caller can filter without a second read.
        Args:
            container_name (str): The container to chart.
            bucket (LogBucket): The bucket width, which picks the window.
            level (str | None): Keep only this level in the series.
        Returns:
            return (LogChartType): The series, its min, max and mean, and
                the levels the window holds.
        """
        end = date_utils.utc_now()
        start = end - bucket.span

        search = self.search().filter(
            "range", **{"@timestamp": {"gte": start, "lte": end}}
        )

        for name, field in (
            ("levels", "log.level"),
            ("containers", "container.name"),
        ):
            search.aggs.bucket(
                "f_" + name, "terms", field=field, size=MAX_FACET
            )

        narrowing = [Q("term", **{"container.name": container_name})]
        if level:
            narrowing.append(Q("term", **{"log.level": level}))
        window = search.aggs.bucket(
            "window", "filter", filter=Q("bool", filter=narrowing)
        )
        window.bucket(
            "timeline",
            "date_histogram",
            field="@timestamp",
            fixed_interval=bucket,
            min_doc_count=0,
            extended_bounds={
                "min": int(start.timestamp() * 1000),
                "max": int(end.timestamp() * 1000),
            },
        )
        window.pipeline(
            "stats", "stats_bucket", buckets_path="timeline>_count"
        )

        try:
            response = await search.extra(size=0).execute()
        except NotFoundError:
            return LogChartType(
                points=[], min=0, max=0, mean=0.0, levels=[], containers=[]
            )

        window = response.aggregations.window
        stats = window.stats

        def keys(name: str) -> list[str]:
            agg = response.aggregations["f_" + name]
            return [str(point.key) for point in agg.buckets]

        return LogChartType(
            points=[
                PointType(
                    count=int(point.doc_count),
                    timestamp=datetime.fromtimestamp(
                        int(point.key) / 1000, UTC
                    ),
                )
                for point in window.timeline.buckets
            ],
            min=int(stats.min or 0),
            max=int(stats.max or 0),
            mean=round(stats.avg or 0.0, 2),
            levels=keys("levels"),
            containers=keys("containers"),
        )

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
            q=q, request_id=request_id, start=start, end=end
        )

        for name, field in (
            ("levels", "log.level"),
            ("loggers", "log.logger"),
            ("containers", "container.name"),
        ):
            search.aggs.bucket(
                "f_" + name, "terms", field=field, size=MAX_FACET
            )

        narrowing = [
            Q("terms", **{field: list(values)})
            for field, values in (
                ("log.level", levels),
                ("log.logger", loggers),
                ("container.name", containers),
            )
            if values
        ]
        if narrowing:
            search = search.post_filter(Q("bool", filter=narrowing))

        start_at = min(offset, MAX_WINDOW - limit)
        search = search.sort("-@timestamp").extra(track_total_hits=True)

        try:
            response = await search[start_at : start_at + limit].execute()
        except NotFoundError:
            return LogPageType(items=[], total_items=0)

        def counts(name: str) -> dict[str, int]:
            agg = response.aggregations["f_" + name]
            return {
                str(point.key): int(point.doc_count)
                for point in agg.buckets
            }

        total = response.to_dict()["hits"]["total"]["value"]
        return LogPageType(
            items=list(response.hits),
            total_items=total,
            levels=counts("levels"),
            loggers=counts("loggers"),
            containers=counts("containers"),
        )
