from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Sequence, cast

import pytest

from src.common.errors.exceptions import NotFoundException
from src.infra.redis.client import RedisClient
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.bubbles.domain.models import BubbleConfigModel
from src.modules.price.calculator.app.services import BubbleCalculatorService
from src.modules.price.calculator.domain.context import BubbleContext
from src.modules.price.calculator.infra.cache import BubbleCache
from src.modules.price.calculator.infra.readers import BubbleReader
from src.modules.price.engine.domain.results import SourceBubbleResult
from src.modules.price.engine.interfaces import ICacheReaderService
from tests.unit.calculator.test_asset_price_cache import _FakeRedis

_at = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def _context(
    bubble_id: int = 1,
    code: AssetCode = AssetCode.GOLD18,
    agg: AggregationType = AggregationType.MEDIAN,
) -> BubbleContext:
    config = BubbleConfigModel(
        bubble_id=bubble_id,
        scheduler_on=True,
        scheduler_seconds=60,
        agg_type=agg,
    )
    return BubbleContext(code=code, bubble_id=bubble_id, config=config)


def _published(
    amount: int,
    asset_id: int = 1,
    source_id: int = 1,
    priced_at: datetime = _at,
) -> SourceBubbleResult:
    return SourceBubbleResult(
        asset_id=asset_id,
        source_id=source_id,
        amount=amount,
        priced_at=priced_at,
    )


class _FakeBubbleReader:

    def __init__(self, contexts: Sequence[BubbleContext]) -> None:
        self.contexts = contexts

    async def get_all(self) -> Sequence[BubbleContext]:
        return self.contexts

    async def get_bubble_config(self, bubble_id: int) -> BubbleContext | None:
        found = None
        for context in self.contexts:
            if context.bubble_id == bubble_id:
                found = context
        return found


class _FakeCacheReader:

    def __init__(
        self,
        premiums: dict[AssetCode, Sequence[SourceBubbleResult]],
    ) -> None:
        self.premiums = premiums

    async def get_bubbles_by_asset(
        self, code: AssetCode
    ) -> Sequence[SourceBubbleResult]:
        return self.premiums.get(code, [])

    async def get_all_bubbles(
        self,
    ) -> dict[AssetCode, Sequence[SourceBubbleResult]]:
        return dict(self.premiums)


def _service(
    contexts: Sequence[BubbleContext],
    premiums: dict[AssetCode, Sequence[SourceBubbleResult]],
) -> tuple[BubbleCalculatorService, BubbleCache]:
    client = cast(RedisClient, SimpleNamespace(client=_FakeRedis()))
    cache = BubbleCache(client)
    service = BubbleCalculatorService(
        cast(BubbleReader, _FakeBubbleReader(contexts)),
        cast(ICacheReaderService, _FakeCacheReader(premiums)),
        cache,
    )
    return service, cache


class TestCalculateOne:
    async def test_the_median_publisher_settles_the_premium(self) -> None:
        service, _ = _service(
            [_context()],
            {
                AssetCode.GOLD18: [
                    _published(2_000_000, source_id=1),
                    _published(3_000_000, source_id=2),
                    _published(7_000_000, source_id=3),
                ]
            },
        )

        amount = await service.calculate(1)

        assert amount == 3_000_000

    async def test_the_settled_premium_lands_in_the_cache(self) -> None:
        service, cache = _service(
            [_context()], {AssetCode.GOLD18: [_published(3_241_000)]}
        )

        await service.calculate(1)
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.amount == 3_241_000
        assert found.asset_id == 1
        assert found.priced_at == _at

    async def test_a_market_under_parity_settles_negative(self) -> None:
        service, cache = _service(
            [_context()],
            {
                AssetCode.GOLD18: [
                    _published(-2_137_540, source_id=1),
                    _published(-2_100_000, source_id=2),
                ]
            },
        )

        amount = await service.calculate(1)

        assert amount == -2_118_770
        assert await cache.get(AssetCode.GOLD18) is not None

    async def test_each_bubble_folds_by_its_own_rule(self) -> None:
        service, _ = _service(
            [_context(agg=AggregationType.MAX)],
            {
                AssetCode.GOLD18: [
                    _published(2_000_000, source_id=1),
                    _published(7_000_000, source_id=2),
                ]
            },
        )

        amount = await service.calculate(1)

        assert amount == 7_000_000

    async def test_the_premium_is_as_fresh_as_its_freshest_publisher(
        self,
    ) -> None:
        later = _at + timedelta(minutes=5)
        service, cache = _service(
            [_context()],
            {
                AssetCode.GOLD18: [
                    _published(3_000_000, source_id=1),
                    _published(3_000_000, source_id=2, priced_at=later),
                ]
            },
        )

        await service.calculate(1)
        found = await cache.get(AssetCode.GOLD18)

        assert found is not None
        assert found.priced_at == later

    async def test_nobody_published_a_premium(self) -> None:
        service, cache = _service([_context()], {})

        amount = await service.calculate(1)

        assert amount == 0
        assert await cache.get(AssetCode.GOLD18) is None

    async def test_a_bubble_that_does_not_exist(self) -> None:
        service, _ = _service([_context()], {})

        with pytest.raises(NotFoundException):
            await service.calculate(9999)


class TestCalculateAll:
    async def test_it_settles_every_bubble_it_can(self) -> None:
        service, cache = _service(
            [
                _context(bubble_id=1, code=AssetCode.GOLD18),
                _context(bubble_id=2, code=AssetCode.USD),
            ],
            {
                AssetCode.GOLD18: [_published(3_241_000, asset_id=1)],
                AssetCode.USD: [_published(500_000, asset_id=2)],
            },
        )

        settled = await service.calculate_all()
        found = await cache.get_all()

        assert settled == 2
        assert {code: r.amount for code, r in found.items()} == {
            AssetCode.GOLD18: 3_241_000,
            AssetCode.USD: 500_000,
        }

    async def test_a_bubble_nobody_published_is_skipped(self) -> None:
        service, cache = _service(
            [
                _context(bubble_id=1, code=AssetCode.GOLD18),
                _context(bubble_id=2, code=AssetCode.USD),
            ],
            {AssetCode.GOLD18: [_published(3_241_000, asset_id=1)]},
        )

        settled = await service.calculate_all()
        found = await cache.get_all()

        assert settled == 1
        assert list(found) == [AssetCode.GOLD18]

    async def test_a_sweep_with_nothing_published_writes_nothing(
        self,
    ) -> None:
        service, cache = _service([_context()], {})

        settled = await service.calculate_all()

        assert settled == 0
        assert await cache.get_all() == {}

    async def test_a_sweep_without_a_single_bubble(self) -> None:
        service, _ = _service([], {AssetCode.GOLD18: [_published(1)]})

        settled = await service.calculate_all()

        assert settled == 0
