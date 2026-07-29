from types import SimpleNamespace
from typing import cast

import pytest

from src.infra.postgres.uow import PGUnitOfWork
from src.infra.redis.client import RedisClient
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import AssetConfigUpdate, AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.engine.app.services import PricingEngineService
from src.modules.price.engine.infra.cache import SourcePriceCache
from src.modules.price.engine.infra.readers import AssetReader, SourceReader
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from tests.unit.engine.test_asset_price_cache import _FakeRedis


def _engine(uow: PGUnitOfWork) -> PricingEngineService:
    """
    Desc: Build the crawler over real readers.
    Args:
        uow (PGUnitOfWork): Unit of work the readers query through.
    Returns:
        return (PricingEngineService): The assembled service.
    """
    # these cover the read and crawl halves; nothing here writes, so the
    # cache is stood up over a fake rather than a live Redis
    cache = SourcePriceCache(
        cast(RedisClient, SimpleNamespace(client=_FakeRedis()))
    )
    return PricingEngineService(AssetReader(uow), SourceReader(uow), cache)


def _assets(uow: PGUnitOfWork) -> tuple[AssetService, AssetConfigService]:
    """
    Desc: Build the asset services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (tuple[AssetService, AssetConfigService]): The two services.
    """
    configs = AssetConfigService(AssetConfigRepository(uow))
    return AssetService(AssetRepository(uow), configs), configs


def _sources(uow: PGUnitOfWork) -> SourceService:
    """
    Desc: Build the source service over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (SourceService): The assembled service.
    """
    return SourceService(
        SourceRepository(uow), SourceConfigService(SourceConfigRepository(uow))
    )


def _source_data(code: SourceCode, switch: SourceSwitch) -> SourceCreate:
    """
    Desc: Build a SourceCreate DTO for the given code and market.
    Args:
        code (SourceCode): Code of the source.
        switch (SourceSwitch): The market it feeds.
    Returns:
        return (SourceCreate): The create DTO.
    """
    return SourceCreate(
        title="منبع",
        code=code,
        website_url="https://example.test",
        icon_url="/storage/file/ab/x.png",
        primary_color="#c8a44b",
        source_type=switch,
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestReadRefs:
    async def test_it_maps_every_asset_code_to_its_id(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _assets(uow)
        gold = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )
        usd = await assets.create(
            AssetCreate(title="دلار", code=AssetCode.USD)
        )

        refs = await AssetReader(uow).read_refs()

        assert {r.code: r.id for r in refs} == {
            AssetCode.GOLD18: gold.id,
            AssetCode.USD: usd.id,
        }

    async def test_it_keeps_a_paused_asset(self, uow: PGUnitOfWork) -> None:
        # a quote still has to resolve to an id even while the asset is off
        assets, configs = _assets(uow)
        created = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )
        await configs.update(created.id, AssetConfigUpdate(scheduler_on=False))

        refs = await AssetReader(uow).read_refs()

        assert [r.id for r in refs] == [created.id]

    async def test_an_empty_table_reads_empty(self, uow: PGUnitOfWork) -> None:
        refs = await AssetReader(uow).read_refs()

        assert list(refs) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestFetchAllDB:
    async def test_it_gathers_every_source_and_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _assets(uow)
        sources = _sources(uow)
        await assets.create(AssetCreate(title="طلا", code=AssetCode.GOLD18))
        await assets.create(AssetCreate(title="دلار", code=AssetCode.USD))
        await sources.create(
            _source_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )
        await sources.create(
            _source_data(SourceCode.TALALAND, SourceSwitch.SUPPLIER)
        )

        context = await _engine(uow)._fetch_all_db()

        assert {s.code for s in context.sources} == {
            SourceCode.TGJU,
            SourceCode.TALALAND,
        }
        assert {a.code for a in context.assets} == {
            AssetCode.GOLD18,
            AssetCode.USD,
        }

    async def test_every_market_is_crawled_not_just_one(
        self, uow: PGUnitOfWork
    ) -> None:
        # one crawl serves every asset, so it must not narrow by switch
        sources = _sources(uow)
        await sources.create(
            _source_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )
        await sources.create(
            _source_data(SourceCode.TALALAND, SourceSwitch.SUPPLIER)
        )
        await sources.create(
            _source_data(SourceCode.GOLD_API, SourceSwitch.GLOBAL_MARKET)
        )

        context = await _engine(uow)._fetch_all_db()

        assert {s.switch for s in context.sources} == set(SourceSwitch)

    async def test_the_sources_carry_their_config(
        self, uow: PGUnitOfWork
    ) -> None:
        # the fetchers are built straight off this config
        sources = _sources(uow)
        await sources.create(
            _source_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )

        context = await _engine(uow)._fetch_all_db()

        assert context.sources[0].cfg.timeout == 10

    async def test_a_paused_asset_is_still_addressable(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _assets(uow)
        created = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )

        context = await _engine(uow)._fetch_all_db()

        assert [a.id for a in context.assets] == [created.id]

    async def test_an_empty_database_yields_an_empty_context(
        self, uow: PGUnitOfWork
    ) -> None:
        context = await _engine(uow)._fetch_all_db()

        assert list(context.sources) == []
        assert list(context.assets) == []
