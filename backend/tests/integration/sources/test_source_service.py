import pytest

from src.common.errors.exceptions import NotFoundException, ValidationException
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.modules.price.sources.domain.dtos import (
    SourceConfigUpdate,
    SourceCreate,
    SourceSearch,
    SourceUpdate,
)
from src.modules.price.sources.domain.enums import (
    ErrorType,
    SourceCode,
    SourceSwitch,
)
from src.modules.price.sources.domain.errors import SourceErrorInfo
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)


def _services(uow: PGUnitOfWork) -> tuple[SourceService, SourceConfigService]:
    """
    Desc: Build the source and source-config services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to read and write through.
    Returns:
        return (tuple[SourceService, SourceConfigService]): The two services.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    sources = SourceService(SourceRepository(uow), configs)
    return sources, configs


def _create_data(
    code: SourceCode = SourceCode.TGJU,
    switch: SourceSwitch = SourceSwitch.IRAN_MARKET,
) -> SourceCreate:
    """
    Desc: Build a SourceCreate DTO for the given code and market.
    Args:
        code (SourceCode): Code of the source to create.
        switch (SourceSwitch): The market it feeds.
    Returns:
        return (SourceCreate): The create DTO.
    """
    return SourceCreate(
        title="شبکه اطلاع‌رسانی طلا و ارز",
        code=code,
        website_url="https://www.tgju.org",
        icon_url="/storage/file/ab/tgju.png",
        primary_color="#c8a44b",
        source_type=switch,
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceServiceCRUD:
    async def test_create_returns_persisted_source(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)

        source = await sources.create(_create_data())

        assert source.id is not None
        assert source.code == SourceCode.TGJU
        assert source.website_url == "https://www.tgju.org"
        assert source.source_type == SourceSwitch.IRAN_MARKET
        assert source.error is None

    async def test_create_also_creates_the_default_config(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, configs = _services(uow)

        source = await sources.create(_create_data())

        config = await configs.get_by_source_id(source.id)
        assert config.source_id == source.id
        assert config.timeout == 10
        assert config.headers_credentials is None
        assert config.auth_credentials is None

    async def test_create_persists_a_long_url(self, uow: PGUnitOfWork) -> None:
        # the column was 55 chars, too short for a real endpoint
        sources, _ = _services(uow)
        url = "https://api.metalpriceapi.com/v1/latest" + "?x=" + "y" * 150
        data = _create_data(SourceCode.METALPRICE_API)
        data.website_url = url

        source = await sources.create(data)

        assert source.website_url == url

    async def test_get_by_id_returns_source(self, uow: PGUnitOfWork) -> None:
        sources, _ = _services(uow)
        created = await sources.create(_create_data())

        fetched = await sources.get_by_id(created.id)

        assert fetched.id == created.id

    async def test_get_by_id_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await sources.get_by_id(9999)

    async def test_get_all_returns_every_source(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        await sources.create(_create_data(SourceCode.TGJU))
        await sources.create(_create_data(SourceCode.NAVASAN))

        found = await sources.get_all()

        assert {s.code for s in found} == {
            SourceCode.TGJU,
            SourceCode.NAVASAN,
        }

    async def test_update_patches_only_set_fields(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        created = await sources.create(_create_data())

        updated = await sources.update(
            created.id, SourceUpdate(primary_color="#ffffff")
        )

        assert updated.primary_color == "#ffffff"
        assert updated.website_url == "https://www.tgju.org"
        assert updated.code == SourceCode.TGJU

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        created = await sources.create(_create_data())

        with pytest.raises(ValidationException):
            await sources.update(created.id, SourceUpdate())

    async def test_update_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await sources.update(9999, SourceUpdate(title="ناموجود"))

    async def test_remove_deletes_source(self, uow: PGUnitOfWork) -> None:
        sources, _ = _services(uow)
        created = await sources.create(_create_data())

        removed = await sources.remove(created.id)

        assert removed.id == created.id
        with pytest.raises(NotFoundException):
            await sources.get_by_id(created.id)

    async def test_remove_cascades_to_the_config(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, configs = _services(uow)
        created = await sources.create(_create_data())

        await sources.remove(created.id)

        with pytest.raises(NotFoundException):
            await configs.get_by_source_id(created.id)


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceError:
    async def test_mark_failed_records_the_error(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        created = await sources.create(_create_data())
        error: SourceErrorInfo = {
            "kind": ErrorType.HTTP_ERROR,
            "message": "gateway timed out",
            "status_code": 504,
        }

        updated = await sources.mark_failed(created.id, error)

        assert updated.error is not None
        assert updated.error["status_code"] == 504
        assert updated.error["kind"] == ErrorType.HTTP_ERROR

    async def test_clear_error_wipes_it(self, uow: PGUnitOfWork) -> None:
        sources, _ = _services(uow)
        created = await sources.create(_create_data())
        await sources.mark_failed(
            created.id,
            {"kind": ErrorType.LOGICAL_ERROR, "message": "bad payload"},
        )

        cleared = await sources.clear_error(created.id)

        assert cleared.error is None

    async def test_mark_failed_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)

        with pytest.raises(NotFoundException):
            await sources.mark_failed(
                9999, {"kind": ErrorType.HTTP_ERROR, "message": "gone"}
            )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceWithConfig:
    async def test_get_all_with_config_eager_loads_the_config(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        await sources.create(_create_data(SourceCode.TGJU))
        await sources.create(_create_data(SourceCode.NAVASAN))

        found = await sources.get_all_with_config()

        assert len(found) == 2
        for source in found:
            assert source.config is not None
            assert source.config.source_id == source.id

    async def test_get_by_switch_narrows_to_one_market(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        await sources.create(
            _create_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )
        await sources.create(
            _create_data(SourceCode.GOLDAPI_IO, SourceSwitch.GLOBAL_MARKET)
        )
        await sources.create(
            _create_data(SourceCode.GOLDIKA, SourceSwitch.SUPPLIER)
        )

        found = await sources.get_by_switch_with_config(
            SourceSwitch.GLOBAL_MARKET
        )

        assert [s.code for s in found] == [SourceCode.GOLDAPI_IO]
        assert found[0].config is not None

    async def test_get_by_switch_on_an_empty_market(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        await sources.create(
            _create_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )

        found = await sources.get_by_switch_with_config(SourceSwitch.SUPPLIER)

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceSearch:
    async def _seed(self, uow: PGUnitOfWork) -> SourceService:
        """
        Desc: Create one source per market for the search tests.
        Args:
            uow (PGUnitOfWork): Unit of work to write through.
        Returns:
            return (SourceService): The service the sources were made with.
        """
        sources, _ = _services(uow)
        await sources.create(
            _create_data(SourceCode.TGJU, SourceSwitch.IRAN_MARKET)
        )
        await sources.create(
            _create_data(SourceCode.GOLDAPI_IO, SourceSwitch.GLOBAL_MARKET)
        )
        await sources.create(
            _create_data(SourceCode.GOLDIKA, SourceSwitch.SUPPLIER)
        )
        return sources

    async def test_an_empty_search_pages_everything(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(SourceSearch())

        assert paged.total_items == 3
        assert len(paged.items) == 3

    async def test_the_page_window_is_applied(self, uow: PGUnitOfWork) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(SourceSearch(page=2, per_page=2))

        assert paged.total_items == 3
        assert len(paged.items) == 1

    async def test_free_text_matches_the_code(self, uow: PGUnitOfWork) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(SourceSearch(q="goldapi"))

        assert [s.code for s in paged.items] == [SourceCode.GOLDAPI_IO]

    async def test_free_text_matches_the_title(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(SourceSearch(q="طلا و ارز"))

        assert paged.total_items == 3

    async def test_a_pasted_public_id_matches(self, uow: PGUnitOfWork) -> None:
        sources = await self._seed(uow)
        target = (await sources.get_all())[0]
        public_id = SOURCE_ID_ENCRYPTION.encode(target.id)

        paged = await sources.get_page(SourceSearch(q=str(public_id)))

        assert [s.id for s in paged.items] == [target.id]

    async def test_source_types_narrow_to_the_checked_markets(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(
            SourceSearch(
                source_types=[
                    SourceSwitch.GLOBAL_MARKET,
                    SourceSwitch.SUPPLIER,
                ]
            )
        )

        assert paged.total_items == 2
        assert {s.code for s in paged.items} == {
            SourceCode.GOLDAPI_IO,
            SourceCode.GOLDIKA,
        }

    async def test_an_empty_source_types_list_filters_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(SourceSearch(source_types=[]))

        assert paged.total_items == 3

    async def test_has_error_keeps_only_failing_sources(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = await self._seed(uow)
        broken = (await sources.get_all())[0]
        await sources.mark_failed(
            broken.id, {"kind": ErrorType.HTTP_ERROR, "message": "timeout"}
        )

        failing = await sources.get_page(SourceSearch(has_error=True))
        healthy = await sources.get_page(SourceSearch(has_error=False))

        assert [s.id for s in failing.items] == [broken.id]
        assert healthy.total_items == 2

    async def test_filters_combine(self, uow: PGUnitOfWork) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(
            SourceSearch(q="gold", source_types=[SourceSwitch.SUPPLIER])
        )

        assert [s.code for s in paged.items] == [SourceCode.GOLDIKA]

    async def test_a_search_that_matches_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        sources = await self._seed(uow)

        paged = await sources.get_page(SourceSearch(q="nothing-here"))

        assert paged.total_items == 0
        assert list(paged.items) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSourceConfigService:
    async def test_update_patches_only_set_fields(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, configs = _services(uow)
        source = await sources.create(_create_data())

        updated = await configs.update(
            source.id, SourceConfigUpdate(timeout=30)
        )

        assert updated.timeout == 30
        assert updated.auth_credentials is None

    async def test_update_writes_the_credentials(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, configs = _services(uow)
        source = await sources.create(_create_data())

        updated = await configs.update(
            source.id,
            SourceConfigUpdate(
                headers_credentials={"X-Api-Key": "k"},
                auth_credentials={"token": "t"},
            ),
        )

        assert updated.headers_credentials == {"X-Api-Key": "k"}
        assert updated.auth_credentials == {"token": "t"}
        assert updated.timeout == 10

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, configs = _services(uow)
        source = await sources.create(_create_data())

        with pytest.raises(ValidationException):
            await configs.update(source.id, SourceConfigUpdate())

    async def test_update_missing_raises_not_found(
        self, uow: PGUnitOfWork
    ) -> None:
        _, configs = _services(uow)

        with pytest.raises(NotFoundException):
            await configs.update(9999, SourceConfigUpdate(timeout=30))

    async def test_get_all_returns_one_config_per_source(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, configs = _services(uow)
        first = await sources.create(_create_data(SourceCode.TGJU))
        second = await sources.create(_create_data(SourceCode.NAVASAN))

        found = await configs.get_all()

        assert {c.source_id for c in found} == {first.id, second.id}


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestGetByIds:
    async def test_it_reads_only_the_sources_asked_for(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        tgju = await sources.create(_create_data(SourceCode.TGJU))
        await sources.create(_create_data(SourceCode.TALALAND))

        found = await sources.get_by_ids([tgju.id])

        assert [source.id for source in found] == [tgju.id]

    async def test_an_id_nothing_carries_is_left_out(
        self, uow: PGUnitOfWork
    ) -> None:
        sources, _ = _services(uow)
        tgju = await sources.create(_create_data(SourceCode.TGJU))

        found = await sources.get_by_ids([tgju.id, 9999])

        assert [source.id for source in found] == [tgju.id]
