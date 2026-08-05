from collections.abc import Awaitable
from typing import TypeVar, cast

from redis.asyncio import Redis

T = TypeVar("T")


async def resolve(value: Awaitable[T] | T) -> T:
    result: T
    if isinstance(value, Awaitable):
        # the isinstance is the proof, but it cannot carry T along with it
        result = await cast("Awaitable[T]", value)
    else:
        result = value
    return result


class RedisClient:
    def __init__(
        self,
        url: str,
        *,
        max_connections: int,
        socket_timeout: float,
        socket_connect_timeout: float,
        health_check_interval: int,
    ) -> None:
        self.client: Redis = Redis.from_url(
            url,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            health_check_interval=health_check_interval,
            decode_responses=True,
        )

    async def close(self) -> None:
        await self.client.aclose()
