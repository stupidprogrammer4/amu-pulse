from datetime import datetime
from typing import Any, Self

from src.common.bases.schemas import BaseMeta, BaseOutput
from src.modules.ops.logs.domain.documents import LogDocument


def _dig(source: dict[str, Any], *path: str) -> Any:
    # Filebeat nests on the dots the formatter wrote flat, so log.level
    # arrives as {"log": {"level": ...}}
    node: Any = source
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


class LogOut(BaseOutput):
    timestamp: datetime
    level: str | None = None
    logger: str | None = None
    message: str = ""
    request_id: str | None = None
    service: str | None = None
    container: str | None = None
    # "logging.py:35 dispatch", where the line was written
    origin: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None

    @classmethod
    def from_doc(cls, doc: LogDocument) -> Self:
        """
        Desc: Flatten one shipped line into the shape a reader wants.
        Args:
            doc (LogDocument): A hit off the log data stream.
        Returns:
            return (Self): The flattened line.
        """
        # to_dict, because @timestamp is not reachable as an attribute and
        # every other field is optional on a line Filebeat could not parse
        src = doc.to_dict()
        file_name = _dig(src, "log", "origin", "file", "name")
        origin = None
        if file_name:
            line = _dig(src, "log", "origin", "file", "line")
            function = _dig(src, "log", "origin", "function")
            origin = f"{file_name}:{line} {function}".strip()
        return cls(
            timestamp=src["@timestamp"],
            level=_dig(src, "log", "level"),
            logger=_dig(src, "log", "logger"),
            message=src.get("message") or "",
            request_id=src.get("request_id"),
            service=_dig(src, "service", "name"),
            container=_dig(src, "container", "name"),
            origin=origin,
            error_type=_dig(src, "error", "type"),
            error_message=_dig(src, "error", "message"),
            stack_trace=_dig(src, "error", "stack_trace"),
        )


class LogMeta(BaseMeta):
    # how many lines of each level the filter matched, so the panel can
    # colour the counts without a second round trip
    levels: dict[str, int] = {}
