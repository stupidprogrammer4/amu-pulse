from collections.abc import AsyncIterator

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.taskiq import TaskiqProvider, setup_dishka
from redis.exceptions import RedisError
from taskiq import InMemoryBroker

import src.tasks.broker
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
from tests.conftest import core_provider_of, test_settings_of


class TaskAssetPriceCache(AssetPriceCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:tasks:assets:price"


class TaskBubbleCache(BubbleCache):
    namespace = "test:tasks:bubble:price"


class TaskSourcePriceCache(SourcePriceCache):
    namespace = "test:tasks:sources:price"


class TaskBubbleSourceCache(BubbleSourceCache):
    namespace = "test:tasks:sources:bubble"


class CacheProvider(Provider):
    """The same caches, under namespaces of the suite's own."""

    scope = Scope.APP

    asset_prices = provide(TaskAssetPriceCache, provides=AssetPriceCache)
    bubbles = provide(TaskBubbleCache, provides=BubbleCache)
    source_prices = provide(TaskSourcePriceCache, provides=SourcePriceCache)
    source_bubbles = provide(TaskBubbleSourceCache, provides=BubbleSourceCache)


@pytest.fixture
async def task_container(integration_settings: Settings, test_dsn: str):
    settings = test_settings_of(integration_settings, test_dsn)
    container = make_async_container(
        TaskiqProvider(),
        core_provider_of(settings),
        *get_bootstrapper().boot_providers(),
        CacheProvider(),
    )
    try:
        yield container
    finally:
        await container.close()


@pytest.fixture
async def broker(task_container) -> AsyncIterator[InMemoryBroker]:
    # a real broker that runs what it is given, on the test container; the
    # tasks are the ones the modules registered, not copies
    running = InMemoryBroker(await_inplace=True)
    running.local_task_registry.update(src.tasks.broker.broker.get_all_tasks())
    setup_dishka(task_container, running)
    await running.startup()
    try:
        yield running
    finally:
        await running.shutdown()


@pytest.fixture
async def caches(task_container) -> AsyncIterator[RedisClient]:
    client = await task_container.get(RedisClient)
    try:
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        pytest.skip(f"redis is not reachable: {exc}")
    written = (
        TaskAssetPriceCache(client),
        TaskBubbleCache(client),
        TaskSourcePriceCache(client),
        TaskBubbleSourceCache(client),
    )
    for cache in written:
        await cache.clear()
    try:
        yield client
    finally:
        for cache in written:
            await cache.clear()
