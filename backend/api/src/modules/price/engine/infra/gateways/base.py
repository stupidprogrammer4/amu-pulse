from abc import ABC, abstractmethod
from typing import Any, Generic, Sequence, TypeVar

import httpx

from src.core.logger import logger
from src.modules.price.engine.domain.quotes import (
    ErrorQuote,
    HTTPErrorQuote,
)
from src.modules.price.sources.domain.enums import ErrorType, SourceCode

user_agent = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)

TQuote = TypeVar("TQuote")


def _body(resp: httpx.Response | None) -> HTTPErrorQuote | None:
    detail = None
    if resp is not None:
        parsed = None
        try:
            decoded = resp.json()
            if isinstance(decoded, dict):
                parsed = {str(k): str(v) for k, v in decoded.items()}
        except ValueError:
            parsed = None
        detail = HTTPErrorQuote(
            raw_content=resp.text[:2000],
            status_code=str(resp.status_code),
            json=parsed,
        )
    return detail


def http_error(exc: httpx.HTTPError) -> ErrorQuote:
    resp = exc.response if isinstance(exc, httpx.HTTPStatusError) else None
    error = ErrorQuote(
        error_type=ErrorType.HTTP_ERROR,
        message=f"{type(exc).__name__}: {exc}",
        http_error=_body(resp),
    )
    return error


def logical_error(exc: Exception) -> ErrorQuote:
    error = ErrorQuote(
        error_type=ErrorType.LOGICAL_ERROR,
        message=f"{type(exc).__name__}: {exc}",
        http_error=None,
    )
    return error


class AbstractFetcher(ABC, Generic[TQuote]):
    __url__: str = ""
    __method__: str = "GET"
    __code__: SourceCode

    default_timeout = 10

    def __init__(
        self,
        headers_credentials: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> None:
        super().__init__()
        self.headers_credentials = headers_credentials or {}
        self.timeout = timeout or self.default_timeout

    async def fetch(self) -> Sequence[TQuote]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                resp = await self._request(client)
                resp.raise_for_status()
                quotes = self._parse(resp)
        except httpx.HTTPError as exc:
            logger.warning(
                "source %s could not be reached: %s",
                self.__code__,
                exc,
                exc_info=exc,
            )
            quotes = self._failed(http_error(exc))
        except Exception as exc:
            logger.error(
                "source %s answered but could not be read: %s",
                self.__code__,
                exc,
                exc_info=exc,
            )
            quotes = self._failed(logical_error(exc))
        return quotes

    async def _request(self, client: httpx.AsyncClient) -> httpx.Response:
        headers = {"User-Agent": user_agent, **self.headers_credentials}
        resp = await client.request(
            method=self.__method__,
            url=self.__url__,
            headers=headers,
        )
        return resp

    @abstractmethod
    def _parse(self, resp: httpx.Response) -> Sequence[TQuote]: ...

    @abstractmethod
    def _failed(self, error: ErrorQuote) -> Sequence[TQuote]: ...


def json_path(payload: Any, *keys: str | int) -> Any:
    node = payload
    for key in keys:
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            raise ValueError(f"missing field {key!r} in response") from None
    return node
