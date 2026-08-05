from __future__ import annotations

import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

import orjson
from rich.logging import RichHandler

from src.core.config import get_settings

#: Per-task correlation id; set by middleware, surfaced on every record.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """
    Desc: Render a record as one ECS-shaped JSON object per line. Filebeat
        reads the container's stdout, decodes the line, and hands the fields
        to Elasticsearch without a grok pattern in between.
    """

    #: Attributes the logging module puts on every record. Anything outside
    #: this set was attached by a caller through ``extra=`` and is shipped.
    BUILTIN_RECORD_ATTRS = frozenset(
        {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "message",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "request_id",
            "stack_info",
            "stacklevel",
            "taskName",
            "thread",
            "threadName",
        }
    )

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "@timestamp": self._timestamp(record.created),
            "log.level": record.levelname.lower(),
            "log.logger": record.name,
            "log.origin.file.name": record.filename,
            "log.origin.file.line": record.lineno,
            "log.origin.function": record.funcName,
            "service.name": self.service,
            "process.thread.name": record.threadName,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            payload["error.type"] = getattr(exc_type, "__name__", None)
            payload["error.message"] = str(exc_value)
            payload["error.stack_trace"] = self.formatException(
                record.exc_info
            )
        elif record.exc_text:
            payload["error.stack_trace"] = record.exc_text

        if record.stack_info:
            payload["log.origin.stack"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key not in self.BUILTIN_RECORD_ATTRS:
                payload[key] = value

        # default=str so an unserialisable extra downgrades to its repr
        # instead of losing the whole line
        return orjson.dumps(payload, default=str).decode()

    @staticmethod
    def _timestamp(created: float) -> str:
        stamp = datetime.fromtimestamp(created, UTC)
        return stamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Logger:
    #: Loggers that ship their own handlers. Left alone they would write a
    #: second, differently formatted copy of every line, which Filebeat
    #: cannot parse.
    ADOPTED_LOGGERS = (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "gunicorn.error",
        "gunicorn.access",
        "taskiq",
    )

    def __init__(
        self, name: str = "app", level: int | str = logging.INFO
    ) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

    def setup(self) -> None:
        """
        Desc: Route every logger in the process through one handler, so a
            container emits a single uniformly formatted stream. Idempotent —
            calling it again swaps the handler rather than stacking a second.
        """
        config = get_settings().logging
        handler = self.build_handler(config.format, config.service)

        root = logging.getLogger()
        for existing in list(root.handlers):
            root.removeHandler(existing)
        root.addHandler(handler)
        root.setLevel(config.level)

        for name in self.ADOPTED_LOGGERS:
            adopted = logging.getLogger(name)
            adopted.handlers.clear()
            adopted.propagate = True

        self.set_level(config.level)

    @staticmethod
    def build_handler(fmt: str, service: str) -> logging.Handler:
        """
        Desc: Build the single handler the whole process logs through.
        Args:
            fmt (str): Either ``console`` or ``json``.
            service (str): Value written to service.name on json records.
        Returns:
            return (logging.Handler): A handler carrying the context filter.
        """
        handler: logging.Handler
        if fmt == "json":
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter(service))
        else:
            handler = RichHandler(rich_tracebacks=True, show_path=False)
            handler.setFormatter(
                logging.Formatter("[%(request_id)s] %(message)s")
            )
        # on the handler, not on a logger: a filter attached to a logger never
        # sees records that propagated up from a child, and uvicorn's do
        handler.addFilter(_ContextFilter())
        return handler

    def set_level(self, level: int | str) -> None:
        self._logger.setLevel(level)

    def debug(self, msg: object, *args: Any, **kw: Any) -> None:
        self._logger.debug(msg, *args, stacklevel=2, **kw)

    def info(self, msg: object, *args: Any, **kw: Any) -> None:
        self._logger.info(msg, *args, stacklevel=2, **kw)

    def warning(self, msg: object, *args: Any, **kw: Any) -> None:
        self._logger.warning(msg, *args, stacklevel=2, **kw)

    def error(self, msg: object, *args: Any, **kw: Any) -> None:
        self._logger.error(msg, *args, stacklevel=2, **kw)

    def exception(self, msg: object, *args: Any, **kw: Any) -> None:
        self._logger.exception(msg, *args, stacklevel=2, **kw)

    def critical(self, msg: object, *args: Any, **kw: Any) -> None:
        self._logger.critical(msg, *args, stacklevel=2, **kw)


logger: Logger = Logger(name="app")

logger.setup()
