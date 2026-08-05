from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from redis.exceptions import RedisError

from src.common.errors.exceptions import NotFoundException
from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient, resolve
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.bubbles.app.services import (
    BubbleConfigService,
    BubbleService,
)
from src.modules.price.bubbles.domain.dtos import (
    BubbleConfigUpdate,
    BubbleCreate,
)
from src.modules.price.bubbles.domain.models import BubbleModel
from src.modules.price.bubbles.infra.repository import (
    BubbleConfigRepository,
    BubbleRepository,
)
from src.modules.price.calculator.app.services import BubbleCalculatorService
from src.modules.price.calculator.infra.cache import BubbleCache
from src.modules.price.calculator.infra.readers import BubbleReader
from src.modules.price.engine.app.services import CacheReaderService
from src.modules.price.engine.domain.results import SourceBubbleResult
from src.modules.price.engine.infra.cache import (
    BubbleSourceCache,
    SourcePriceCache,
)

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


class _TestBubbleCache(BubbleCache):
    # never touch the namespace a running engine is writing to
    namespace = "test:calc:bubble:price"


class _TestBubbleSourceCache(BubbleSourceCache):
    namespace = "test:calc:sources:bubble"


class _TestSourcePriceCache(SourcePriceCache):
    namespace = "test:calc:sources:price"


@pytest.fixture
async def redis(
    integration_settings: Settings,
) -> AsyncIterator[RedisClient]:
    client = RedisClient(
        integration_settings.redis.url,
        max_connections=2,
        socket_timeout=integration_settings.redis.socket_timeout,
        socket_connect_timeout=(
            integration_settings.redis.socket_connect_timeout
        ),
        health_check_interval=(
            integration_settings.redis.health_check_interval
        ),
    )
    try:
        await resolve(client.client.ping())
    except (RedisError, OSError) as exc:
        await client.close()
        pytest.skip(f"redis is not reachable: {exc}")
    settled = _TestBubbleCache(client)
    published = _TestBubbleSourceCache(client)
    await settled.clear()
    await published.clear()
    try:
        yield client
    finally:
        await settled.clear()
        await published.clear()
        await client.close()


def _service(
    uow: PGUnitOfWork,
    redis: RedisClient,
) -> tuple[BubbleCalculatorService, _TestBubbleCache]:
    """
    Desc: Build the service over the real database, redis and engine reader.
    Args:
        uow (PGUnitOfWork): Unit of work the bubbles are read through.
        redis (RedisClient): Client both caches run on.
    Returns:
        return (tuple[BubbleCalculatorService, _TestBubbleCache]): The
            service and the cache it settles into.
    """
    settled = _TestBubbleCache(redis)
    reader = CacheReaderService(
        _TestSourcePriceCache(redis),
        _TestBubbleSourceCache(redis),
    )
    service = BubbleCalculatorService(BubbleReader(uow), reader, settled)
    return service, settled


def _bubbles(uow: PGUnitOfWork) -> tuple[BubbleService, BubbleConfigService]:
    """
    Desc: Build the bubble services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (tuple[BubbleService, BubbleConfigService]): The two services.
    """
    configs = BubbleConfigService(BubbleConfigRepository(uow))
    return BubbleService(BubbleRepository(uow), configs), configs


async def _bubble(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> BubbleModel:
    """
    Desc: Create one bubble with its default config.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Asset whose premium it tracks.
    Returns:
        return (BubbleModel): The created bubble.
    """
    bubbles, _ = _bubbles(uow)
    bubble = await bubbles.create(BubbleCreate(title="حباب", code=code))
    return bubble


def _published(
    amount: int,
    asset_id: int = 1,
    source_id: int = 1,
) -> SourceBubbleResult:
    """
    Desc: Build what one source published as an asset's premium.
    Args:
        amount (int): The premium in rial, signed.
        asset_id (int): ID of the asset it belongs to.
        source_id (int): ID of the source that published it.
    Returns:
        return (SourceBubbleResult): The published premium.
    """
    return SourceBubbleResult(
        asset_id=asset_id,
        source_id=source_id,
        amount=amount,
        priced_at=_at,
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBubbleCalculatorServiceAgainstRealInfra:
    async def test_it_settles_what_the_crawl_published(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        bubble = await _bubble(uow)
        await _TestBubbleSourceCache(redis).set(
            AssetCode.GOLD18,
            [
                _published(2_000_000, source_id=1),
                _published(3_000_000, source_id=2),
                _published(7_000_000, source_id=3),
            ],
        )
        service, cache = _service(uow, redis)

        amount = await service.calculate(bubble.id)
        found = await cache.get(AssetCode.GOLD18)

        assert amount == 3_000_000
        assert found is not None
        assert found.amount == 3_000_000
        assert found.priced_at == _at

    async def test_it_settles_by_the_rule_the_bubble_carries(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        bubble = await _bubble(uow)
        _, configs = _bubbles(uow)
        await configs.update(
            bubble.id, BubbleConfigUpdate(agg_type=AggregationType.MIN)
        )
        await _TestBubbleSourceCache(redis).set(
            AssetCode.GOLD18,
            [
                _published(2_000_000, source_id=1),
                _published(7_000_000, source_id=2),
            ],
        )
        service, _ = _service(uow, redis)

        amount = await service.calculate(bubble.id)

        assert amount == 2_000_000

    async def test_a_bubble_nobody_published_settles_nothing(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        bubble = await _bubble(uow)
        service, cache = _service(uow, redis)

        amount = await service.calculate(bubble.id)

        assert amount == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_a_bubble_that_does_not_exist(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        service, _ = _service(uow, redis)

        with pytest.raises(NotFoundException):
            await service.calculate(9999)

    async def test_the_sweep_settles_every_published_bubble(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        await _bubble(uow)
        await _bubble(uow, AssetCode.USD)
        published = _TestBubbleSourceCache(redis)
        await published.set_many(
            {
                AssetCode.GOLD18: [_published(3_241_000, asset_id=1)],
                AssetCode.USD: [_published(500_000, asset_id=2)],
            }
        )
        service, cache = _service(uow, redis)

        settled = await service.calculate_all()
        found = await cache.get_all()

        assert settled == 2
        assert {code: r.amount for code, r in found.items()} == {
            AssetCode.GOLD18: 3_241_000,
            AssetCode.USD: 500_000,
        }

    async def test_the_sweep_skips_what_the_crawl_never_reached(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        await _bubble(uow)
        await _bubble(uow, AssetCode.USD)
        await _TestBubbleSourceCache(redis).set(
            AssetCode.USD, [_published(500_000, asset_id=2)]
        )
        service, cache = _service(uow, redis)

        settled = await service.calculate_all()
        found = await cache.get_all()

        assert settled == 1
        assert list(found) == [AssetCode.USD]

    async def test_a_sweep_with_no_bubble_at_all(
        self, uow: PGUnitOfWork, redis: RedisClient
    ) -> None:
        service, _ = _service(uow, redis)

        settled = await service.calculate_all()

        assert settled == 0
