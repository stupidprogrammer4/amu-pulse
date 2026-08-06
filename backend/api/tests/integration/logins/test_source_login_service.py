import pytest

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.logins.app.services import SourceLoginService
from src.modules.price.logins.infra import gateways
from src.modules.price.logins.infra.gateways import AbstractLogin
from src.modules.price.logins.infra.readers import LoginReader
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import (
    SourceConfigUpdate,
    SourceCreate,
)
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)


class _GrantingLogin(AbstractLogin):
    async def _issue(self) -> dict[str, str]:
        user = self.source.auth_credentials.get("username", "")
        return {"Authorization": f"Bearer {user}-token"}


class _RefusingLogin(AbstractLogin):
    async def _issue(self) -> dict[str, str]:
        raise RuntimeError("bad password")


def _services(
    uow: PGUnitOfWork,
) -> tuple[SourceLoginService, SourceService, SourceConfigService]:
    configs = SourceConfigService(SourceConfigRepository(uow))
    sources = SourceService(SourceRepository(uow), configs)
    logins = SourceLoginService(LoginReader(uow), configs)
    return logins, sources, configs


def _source_data(code: SourceCode) -> SourceCreate:
    return SourceCreate(
        title="منبع",
        code=code,
        website_url="https://example.test",
        icon_url="/storage/file/ab/x.png",
        primary_color="#c8a44b",
        source_type=SourceSwitch.SUPPLIER,
    )


async def _give_secret(
    configs: SourceConfigService,
    source_id: int,
) -> None:
    await configs.update(
        source_id, SourceConfigUpdate(auth_credentials={"username": "ali"})
    )


@pytest.fixture
def granting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(gateways.LOGINS, SourceCode.MIRROKNI, _GrantingLogin)


@pytest.fixture
def refusing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(gateways.LOGINS, SourceCode.MIRROKNI, _RefusingLogin)


@pytest.mark.usefixtures("migrated_test_db", "clean_db", "granting")
class TestLoginGranted:
    async def test_it_writes_what_the_source_issued(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await configs.update(
            source.id,
            SourceConfigUpdate(auth_credentials={"username": "ali"}),
        )

        issued = await logins.login(SourceCode.MIRROKNI)

        config = await configs.get_by_source_id(source.id)
        assert issued is True
        assert config.headers_credentials == {
            "Authorization": "Bearer ali-token"
        }

    async def test_the_login_secret_is_left_alone(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await configs.update(
            source.id,
            SourceConfigUpdate(auth_credentials={"username": "ali"}),
        )

        await logins.login(SourceCode.MIRROKNI)

        config = await configs.get_by_source_id(source.id)
        assert config.auth_credentials == {"username": "ali"}

    async def test_login_all_covers_every_source_with_a_gateway(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await _give_secret(configs, source.id)
        await sources.create(_source_data(SourceCode.TALALAND))

        saved = await logins.login_all()

        assert saved == 1

    async def test_login_by_id_resolves_the_code(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await _give_secret(configs, source.id)

        issued = await logins.login_by_id(source.id)

        assert issued is True

    async def test_a_second_login_replaces_the_headers(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await configs.update(
            source.id,
            SourceConfigUpdate(
                auth_credentials={"username": "ali"},
                headers_credentials={"Authorization": "old"},
            ),
        )

        await logins.login(SourceCode.MIRROKNI)

        config = await configs.get_by_source_id(source.id)
        assert config.headers_credentials != {"Authorization": "old"}


@pytest.mark.usefixtures("migrated_test_db", "clean_db", "refusing")
class TestLoginRefused:
    async def test_a_refusal_is_not_an_exception(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await _give_secret(configs, source.id)

        issued = await logins.login(SourceCode.MIRROKNI)

        assert issued is False

    async def test_a_refusal_leaves_the_old_headers_in_place(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await configs.update(
            source.id,
            SourceConfigUpdate(
                auth_credentials={"username": "ali"},
                headers_credentials={"Authorization": "old"},
            ),
        )

        await logins.login(SourceCode.MIRROKNI)

        config = await configs.get_by_source_id(source.id)
        assert config.headers_credentials == {"Authorization": "old"}

    async def test_the_quote_carries_why_it_refused(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, configs = _services(uow)
        source = await sources.create(_source_data(SourceCode.MIRROKNI))
        await _give_secret(configs, source.id)

        quotes = await logins._try_to_login_all([SourceCode.MIRROKNI])

        assert len(quotes) == 1
        assert quotes[0].error is not None
        assert "bad password" in quotes[0].error.message
        assert quotes[0].issued is False


@pytest.mark.usefixtures("migrated_test_db", "clean_db", "granting")
class TestLoginSelection:
    async def test_a_code_without_a_gateway_is_skipped(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, _ = _services(uow)
        await sources.create(_source_data(SourceCode.TALALAND))

        saved = await logins.login_codes([SourceCode.TALALAND])

        assert saved == 0

    async def test_a_code_with_no_source_row_is_skipped(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, _, _ = _services(uow)

        saved = await logins.login_codes([SourceCode.MIRROKNI])

        assert saved == 0

    async def test_an_empty_request_touches_nothing(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, _, _ = _services(uow)

        saved = await logins.login_codes([])

        assert saved == 0

    async def test_a_source_without_a_secret_never_reaches_the_gateway(
        self, uow: PGUnitOfWork
    ) -> None:
        logins, sources, _ = _services(uow)
        await sources.create(_source_data(SourceCode.MIRROKNI))

        quotes = await logins._try_to_login_all([SourceCode.MIRROKNI])

        assert list(quotes) == []
