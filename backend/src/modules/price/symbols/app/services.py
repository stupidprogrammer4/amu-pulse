from typing import Sequence

from src.common.bases.services import BaseIDService
from src.modules.price.symbols.domain.dtos import SymbolCreate, SymbolUpdate
from src.modules.price.symbols.domain.models import SymbolModel
from src.modules.price.symbols.infra.repository import SymbolRepository


class SymbolService(BaseIDService[SymbolModel]):
    def __init__(self, repo: SymbolRepository) -> None:
        """
        Desc: Build the service with its repository.
        Args:
            repo (SymbolRepository): The symbol repository.
        """
        self.repo = repo

    async def create(self, data: SymbolCreate) -> SymbolModel:
        """
        Desc: Create a symbol.
        Args:
            data (SymbolCreate): Validated payload to persist.
        Returns:
            return (SymbolModel): The created symbol.
        """
        symbol = await self.repo.create(
            SymbolModel(**data.to_row(exclude_unset=False))
        )
        return symbol

    async def update(self, id: int, data: SymbolUpdate) -> SymbolModel:
        """
        Desc: Patch a symbol by id.
        Args:
            id (int): ID of the symbol.
            data (SymbolUpdate): The fields to change.
        Returns:
            return (SymbolModel): The updated symbol.
        """
        row = self._check_not_empty_dict(data.to_row())
        symbol = await self.repo.update_by_id(id, row)
        symbol = self._check_for_id_existence(id, symbol)
        return symbol

    async def get_by_id(self, id: int) -> SymbolModel:
        """
        Desc: Get a symbol by id.
        Args:
            id (int): ID of the symbol.
        Returns:
            return (SymbolModel): The found symbol.
        """
        symbol = await self.repo.get_by_id(id)
        symbol = self._check_for_id_existence(id, symbol)
        return symbol

    async def get_by_ids(
        self,
        ids: list[int],
    ) -> Sequence[SymbolModel]:
        """
        Desc: Get the symbols the given ids belong to.
        Args:
            ids (list[int]): IDs of the symbols to read.
        Returns:
            return (Sequence[SymbolModel]): The symbols that exist.
        """
        symbols = await self.repo.get_by_ids(ids)
        return symbols

    async def get_all(self) -> Sequence[SymbolModel]:
        """
        Desc: Get every symbol.
        Returns:
            return (Sequence[SymbolModel]): All symbols.
        """
        symbols = await self.repo.get_all()
        return symbols

    async def get_by_asset_id(
        self,
        asset_id: int,
    ) -> Sequence[SymbolModel]:
        """
        Desc: Get every symbol an asset is quoted through.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (Sequence[SymbolModel]): The asset's symbols.
        """
        symbols = await self.repo.get_by_asset_id(asset_id)
        return symbols

    async def remove(self, id: int) -> SymbolModel:
        """
        Desc: Delete a symbol by id.
        Args:
            id (int): ID of the symbol.
        Returns:
            return (SymbolModel): The deleted symbol.
        """
        symbol = await self.repo.delete_by_id(id)
        symbol = self._check_for_id_existence(id, symbol)
        return symbol
