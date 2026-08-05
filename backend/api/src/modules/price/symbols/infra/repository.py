from typing import Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGIDRepository
from src.modules.price.symbols.domain.models import SymbolModel


class SymbolRepository(PGIDRepository[SymbolModel]):
    async def get_by_asset_id(
        self,
        asset_id: int,
    ) -> Sequence[SymbolModel]:
        """
        Desc: Get every symbol of one asset, oldest first.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (Sequence[SymbolModel]): The asset's symbols.
        """
        stmt = (
            select(SymbolModel)
            .where(col(SymbolModel.asset_id) == asset_id)
            .order_by(col(SymbolModel.id))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
