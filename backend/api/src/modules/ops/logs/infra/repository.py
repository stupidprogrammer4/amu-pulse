from collections.abc import Sequence
from datetime import datetime
from typing import Any

from elasticsearch import NotFoundError

from src.infra.es.repository import ESRepository
from src.modules.ops.logs.domain.documents import LogDocument
from src.modules.ops.logs.domain.results import LogPageType

# Elasticsearch refuses from + size past this without a search_after cursor;
# a reader paging that deep wants a filter, not another page.
MAX_WINDOW = 10_000


class LogRepository(ESRepository[LogDocument]):
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
        search = self.search()

        # the Elasticsearch field names stop here: a caller asks for a
        # level, not for a terms clause on log.level
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

        search.aggs.bucket("levels", "terms", field="log.level", size=10)

        start_at = min(offset, MAX_WINDOW - limit)
        search = search.sort("-@timestamp").extra(track_total_hits=True)

        try:
            response = await search[start_at : start_at + limit].execute()
        except NotFoundError:
            # nothing has been shipped yet, so the stream does not exist.
            # An empty page is the honest answer; a 404 would read as a bad
            # request rather than as a quiet system.
            return LogPageType(items=[], total_items=0)

        level_counts = {
            bucket.key: bucket.doc_count
            for bucket in response.aggregations.levels.buckets
        }
        # off the raw body: the hit list is typed as a plain list, so the
        # total the response carries alongside it is not reachable from it
        total = response.to_dict()["hits"]["total"]["value"]
        return LogPageType(
            items=list(response.hits),
            total_items=total,
            levels=level_counts,
        )
