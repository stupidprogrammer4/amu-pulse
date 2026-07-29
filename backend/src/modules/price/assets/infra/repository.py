from typing import Any, Optional, Sequence

from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlmodel import col, select

from src.infra.postgres.repository.base import (
    PGIDRepository,
    PGTimestampRepository,
)
from src.modules.price.assets.domain.models import AssetConfigModel, AssetModel


class AssetRepository(PGIDRepository[AssetModel]):
    async def get_all_with_config(self) -> Sequence[AssetModel]:
        """
        Desc: Get every asset with its config eagerly loaded, oldest first.
        Returns:
            return (Sequence[AssetModel]): All assets, each carrying its
                config.
        """
        stmt = (
            select(AssetModel)
            .options(joinedload(AssetModel.config, innerjoin=True))
            .order_by(col(AssetModel.id))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()


class AssetConfigRepository(PGTimestampRepository[AssetConfigModel]):
    async def get_by_asset_id(
        self,
        asset_id: int,
    ) -> Optional[AssetConfigModel]:
        """
        Desc: Get an asset's config by the asset it belongs to.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (Optional[AssetConfigModel]): Found config or None.
        """
        stmt = select(AssetConfigModel).where(
            col(AssetConfigModel.asset_id) == asset_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_asset_id(
        self,
        asset_id: int,
        row: dict[str, Any],
    ) -> Optional[AssetConfigModel]:
        """
        Desc: Patch an asset's config from a column dict.
        Args:
            asset_id (int): ID of the owning asset.
            row (dict[str, Any]): Column values to write.
        Returns:
            return (Optional[AssetConfigModel]): Updated config or None.
        """
        stmt = (
            update(AssetConfigModel)
            .where(col(AssetConfigModel.asset_id) == asset_id)
            .values(**row)
            .returning(AssetConfigModel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
