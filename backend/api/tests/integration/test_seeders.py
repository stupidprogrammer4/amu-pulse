import pytest

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.seeders.assets import ASSETS, seed_assets
from src.seeders.sources import SOURCES, seed_sources
from tests.conftest import NullScheduler


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestAssetSeeder:
    async def test_it_creates_every_declared_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_assets(uow)

        assert len(created) == len(ASSETS)
        assert {a.code for a in created} == {s.code for s in ASSETS}

    async def test_every_seeded_asset_gets_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_assets(uow)
        configs = AssetConfigService(
            AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
        )

        for asset in created:
            config = await configs.get_by_asset_id(asset.id)
            assert config.asset_id == asset.id

    async def test_running_it_twice_creates_nothing_new(
        self, uow: PGUnitOfWork
    ) -> None:
        await seed_assets(uow)

        second = await seed_assets(uow)

        assert second == []
        service = AssetService(
            AssetRepository(uow),
            AssetConfigService(
                AssetConfigRepository(uow),
                AssetRepository(uow),
                NullScheduler(),
            ),
        )
        assert len(await service.get_all()) == len(ASSETS)


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceSeeder:
    async def test_it_creates_every_declared_source(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_sources(uow)

        assert len(created) == len(SOURCES)
        assert {s.code for s in created} == {s.code for s in SOURCES}

    async def test_it_covers_every_source_code(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_sources(uow)

        assert {s.code for s in created} == set(SourceCode)

    async def test_every_market_is_represented(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_sources(uow)

        assert {s.source_type for s in created} == set(SourceSwitch)

    async def test_every_seeded_source_gets_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        await seed_sources(uow)
        configs = SourceConfigService(SourceConfigRepository(uow))

        found = await configs.get_all()

        assert len(found) == len(SOURCES)

    async def test_the_icon_url_points_at_the_favicon_service(
        self, uow: PGUnitOfWork
    ) -> None:
        created = await seed_sources(uow)

        for source in created:
            assert source.icon_url.startswith("https://www.google.com/")

    async def test_running_it_twice_creates_nothing_new(
        self, uow: PGUnitOfWork
    ) -> None:
        await seed_sources(uow)

        second = await seed_sources(uow)

        assert second == []
        service = SourceService(
            SourceRepository(uow),
            SourceConfigService(SourceConfigRepository(uow)),
        )
        assert len(await service.get_all()) == len(SOURCES)
