import pytest

from src.infra.postgres.uow import PGUnitOfWork
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
from tests.conftest import NullScheduler


def _assets(uow: PGUnitOfWork) -> tuple[AssetService, AssetConfigService]:
    """
    Desc: Build the asset services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (tuple[AssetService, AssetConfigService]): The two services.
    """
    configs = AssetConfigService(
        AssetConfigRepository(uow), AssetRepository(uow), NullScheduler()
    )
    return AssetService(AssetRepository(uow), configs), configs


def _sources(uow: PGUnitOfWork) -> SourceService:
    """
    Desc: Build the source service over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (SourceService): The assembled service.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    return SourceService(SourceRepository(uow), configs)


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
class TestAssetReader:
    async def test_it_reads_an_asset_with_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        assets, _ = _assets(uow)
        created = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )

        context = await AssetReader(uow).read(created.id)

        assert context is not None
        assert context.id == created.id
        assert context.code == AssetCode.GOLD18
        assert context.cfg.asset_id == created.id
        assert context.cfg.scheduler_seconds == 60

    async def test_a_missing_asset_reads_as_none(
        self, uow: PGUnitOfWork
    ) -> None:
        context = await AssetReader(uow).read(9999)

        assert context is None

    async def test_read_scheduled_keeps_only_enabled_assets(
        self, uow: PGUnitOfWork
    ) -> None:
        # the dollar is on from birth; gold waits to be switched on
        assets, configs = _assets(uow)
        gold = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )
        dollar = await assets.create(
            AssetCreate(title="دلار", code=AssetCode.USD)
        )

        paused = await AssetReader(uow).read_scheduled()
        await configs.update(gold.id, AssetConfigUpdate(scheduler_on=True))
        found = await AssetReader(uow).read_scheduled()

        assert [c.id for c in paused] == [dollar.id]
        assert [c.id for c in found] == [gold.id, dollar.id]

    async def test_a_brand_new_asset_is_not_swept(
        self, uow: PGUnitOfWork
    ) -> None:
        # creating an asset must not start polling endpoints nobody set up
        assets, _ = _assets(uow)
        await assets.create(AssetCreate(title="طلا", code=AssetCode.GOLD18))

        found = await AssetReader(uow).read_scheduled()

        assert list(found) == []

    async def test_an_explicit_read_ignores_the_scheduler_flag(
        self, uow: PGUnitOfWork
    ) -> None:
        # a manual repricing must still work on a paused asset
        assets, _ = _assets(uow)
        created = await assets.create(
            AssetCreate(title="طلا", code=AssetCode.GOLD18)
        )

        context = await AssetReader(uow).read(created.id)

        assert context is not None
        assert context.cfg.scheduler_on is False

    async def test_read_scheduled_on_an_empty_table(
        self, uow: PGUnitOfWork
    ) -> None:
        found = await AssetReader(uow).read_scheduled()

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceReader:
    async def test_it_reads_every_source_with_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = _sources(uow)
        await sources.create(
            _source_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )
        await sources.create(
            _source_data(SourceCode.TALALAND, SourceSwitch.SUPPLIER)
        )

        found = await SourceReader(uow).read_all()

        assert {c.code for c in found} == {
            SourceCode.TGJU,
            SourceCode.TALALAND,
        }
        assert all(c.cfg.timeout == 10 for c in found)

    async def test_read_by_switch_narrows_to_one_market(
        self, uow: PGUnitOfWork
    ) -> None:
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

        found = await SourceReader(uow).read_by_switch(SourceSwitch.SUPPLIER)

        assert [c.code for c in found] == [SourceCode.TALALAND]
        assert found[0].switch == SourceSwitch.SUPPLIER

    async def test_a_market_with_no_sources_reads_empty(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = _sources(uow)
        await sources.create(
            _source_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )

        found = await SourceReader(uow).read_by_switch(SourceSwitch.SUPPLIER)

        assert list(found) == []

    async def test_the_context_carries_the_credentials(
        self, uow: PGUnitOfWork
    ) -> None:
        # the fetchers are built from exactly this config
        sources = _sources(uow)
        created = await sources.create(
            _source_data(SourceCode.TALALAND, SourceSwitch.SUPPLIER)
        )
        configs = SourceConfigService(SourceConfigRepository(uow))
        await configs.repo.update_by_source_id(
            created.id, {"auth_credentials": {"token": "t"}}
        )

        found = await SourceReader(uow).read_all()

        assert found[0].cfg.auth_credentials == {"token": "t"}
