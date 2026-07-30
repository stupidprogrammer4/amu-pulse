import pytest

from src.common.errors.exceptions import NotFoundException, ValidationException
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.domain.dtos import SymbolCreate, SymbolUpdate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.infra.repository import SymbolRepository


def _service(uow: PGUnitOfWork) -> SymbolService:
    """
    Desc: Build the symbol service over a real repository.
    Args:
        uow (PGUnitOfWork): Unit of work to read and write through.
    Returns:
        return (SymbolService): The service.
    """
    service = SymbolService(SymbolRepository(uow))
    return service


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset for symbols to hang off.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
    configs = AssetConfigService(AssetConfigRepository(uow))
    assets = AssetService(AssetRepository(uow), configs)
    asset = await assets.create(AssetCreate(title="طلا", code=code))
    return asset


def _create(
    asset: AssetModel,
    code: SymbolCode = SymbolCode.GOLD18_GRAM,
    currency: CurrencyType = CurrencyType.RIAL,
) -> SymbolCreate:
    """
    Desc: Build a SymbolCreate pointing at the given asset.
    Args:
        asset (AssetModel): The asset the symbol quotes.
        code (SymbolCode): Code of the symbol.
        currency (CurrencyType): What the line is priced in.
    Returns:
        return (SymbolCreate): The create DTO.
    """
    data = SymbolCreate(
        title="هر گرم طلای ۱۸ عیار",
        code=code,
        asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
        currency=currency,
    )
    return data


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSymbolServiceCRUD:
    async def test_create_returns_persisted_symbol(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        asset = await _asset(uow)

        symbol = await symbols.create(_create(asset))

        assert symbol.id is not None
        assert symbol.code == SymbolCode.GOLD18_GRAM
        assert symbol.asset_id == asset.id
        assert symbol.currency == CurrencyType.RIAL
        assert symbol.description is None

    async def test_one_asset_carries_several_lines(
        self, uow: PGUnitOfWork
    ) -> None:
        # gold is quoted per gram and per mesghal at the same time
        symbols = _service(uow)
        asset = await _asset(uow)

        await symbols.create(_create(asset))
        await symbols.create(_create(asset, SymbolCode.GOLD18_MAZANE))
        found = await symbols.get_by_asset_id(asset.id)

        assert [row.code for row in found] == [
            SymbolCode.GOLD18_GRAM,
            SymbolCode.GOLD18_MAZANE,
        ]

    async def test_get_by_asset_id_reads_only_its_own_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await symbols.create(_create(gold))
        await symbols.create(_create(dollar, SymbolCode.USD_RIAL))

        found = await symbols.get_by_asset_id(dollar.id)

        assert [row.code for row in found] == [SymbolCode.USD_RIAL]

    async def test_get_by_id_returns_symbol(self, uow: PGUnitOfWork) -> None:
        symbols = _service(uow)
        asset = await _asset(uow)
        created = await symbols.create(_create(asset))

        found = await symbols.get_by_id(created.id)

        assert found.id == created.id

    async def test_get_by_id_raises_for_a_missing_symbol(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)

        with pytest.raises(NotFoundException):
            await symbols.get_by_id(4040)

    async def test_get_all_returns_every_symbol(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        asset = await _asset(uow)
        await symbols.create(_create(asset))
        await symbols.create(_create(asset, SymbolCode.GOLD18_MAZANE))

        found = await symbols.get_all()

        assert len(found) == 2

    async def test_update_patches_only_what_is_given(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        asset = await _asset(uow)
        created = await symbols.create(_create(asset))

        updated = await symbols.update(
            created.id, SymbolUpdate(title="مظنه آب‌شده")
        )

        assert updated.title == "مظنه آب‌شده"
        assert updated.code == SymbolCode.GOLD18_GRAM
        assert updated.currency == CurrencyType.RIAL

    async def test_update_empty_patch_raises_validation(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        asset = await _asset(uow)
        created = await symbols.create(_create(asset))

        with pytest.raises(ValidationException):
            await symbols.update(created.id, SymbolUpdate())

    async def test_update_raises_for_a_missing_symbol(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)

        with pytest.raises(NotFoundException):
            await symbols.update(4040, SymbolUpdate(title="مظنه"))

    async def test_remove_returns_the_deleted_symbol(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        asset = await _asset(uow)
        created = await symbols.create(_create(asset))

        deleted = await symbols.remove(created.id)

        assert deleted.id == created.id
        assert await symbols.get_all() == []

    async def test_remove_raises_for_a_missing_symbol(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)

        with pytest.raises(NotFoundException):
            await symbols.remove(4040)

    async def test_deleting_the_asset_takes_its_symbols_with_it(
        self, uow: PGUnitOfWork
    ) -> None:
        symbols = _service(uow)
        configs = AssetConfigService(AssetConfigRepository(uow))
        assets = AssetService(AssetRepository(uow), configs)
        asset = await _asset(uow)
        await symbols.create(_create(asset))

        await assets.remove(asset.id)

        assert await symbols.get_all() == []
