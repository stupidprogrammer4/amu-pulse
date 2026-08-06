from collections.abc import AsyncIterator

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.exceptions import RedisError

import src.tasks.broker  # noqa: F401
from src.core.bootstrap import get_bootstrapper
from src.core.config import Settings
from src.infra.redis.client import RedisClient, resolve
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)
from src.modules.price.engine.infra.cache import (
    BubbleSourceCache,
    SourcePriceCache,
)
from src.web.error_handlers import setup_exception_handlers
from tests.conftest import core_provider_of, test_settings_of


class ApiAssetPriceCache(AssetPriceCache):
    namespace = "test:api:assets:price"


class ApiBubbleCache(BubbleCache):
    namespace = "test:api:bubble:price"


class ApiSourcePriceCache(SourcePriceCache):
    namespace = "test:api:sources:price"


class ApiBubbleSourceCache(BubbleSourceCache):
    namespace = "test:api:sources:bubble"


class CacheProvider(Provider):

    scope = Scope.APP

    asset_prices = provide(ApiAssetPriceCache, provides=AssetPriceCache)
    bubbles = provide(ApiBubbleCache, provides=BubbleCache)
    source_prices = provide(ApiSourcePriceCache, provides=SourcePriceCache)
    source_bubbles = provide(ApiBubbleSourceCache, provides=BubbleSourceCache)


@pytest.fixture
async def api_container(integration_settings: Settings, test_dsn: str):
    settings = test_settings_of(integration_settings, test_dsn)
    container = make_async_container(
        FastapiProvider(),
        core_provider_of(settings),
        *get_bootstrapper().boot_providers(),
        CacheProvider(),
    )
    try:
        yield container
    finally:
        await container.close()


@pytest.fixture
async def caches(api_container) -> AsyncIterator[RedisClient]:
    client = await api_container.get(RedisClient)
    try:
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        pytest.skip(f"redis is not reachable: {exc}")
    written = (
        ApiAssetPriceCache(client),
        ApiBubbleCache(client),
        ApiSourcePriceCache(client),
        ApiBubbleSourceCache(client),
    )
    for cache in written:
        await cache.clear()
    try:
        yield client
    finally:
        for cache in written:
            await cache.clear()


@pytest.fixture
async def client(api_container) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    for router in get_bootstrapper().boot_routers():
        app.include_router(router)
    setup_exception_handlers(app)
    setup_dishka(api_container, app)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as built:
        yield built


@pytest.fixture
async def queue(caches: RedisClient) -> AsyncIterator[str]:
    stream = "calculator_queue"
    before = await resolve(caches.client.xrevrange(stream, count=1))
    last = before[0][0] if before else "0-0"
    yield stream
    queued = await resolve(
        caches.client.xrange(stream, min=f"({last}", max="+")
    )
    for id, _ in queued:
        await resolve(caches.client.xdel(stream, id))
