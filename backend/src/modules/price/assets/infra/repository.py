from typing import Any, Optional, Sequence

from sqlalchemy import delete, update
from sqlalchemy.orm import joinedload
from sqlmodel import col, select

from src.infra.postgres.repository.base import (
    PGIDRepository,
    PGTimestampRepository,
)
from src.modules.price.assets.domain.models import (
    AssetConfigModel,
    AssetModel,
    AssetSwitchModel,
)


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


class AssetSwitchRepository(PGIDRepository[AssetSwitchModel]):
    async def bulk_update(
        self,
        asset_id: int,
        rows: Sequence[AssetSwitchModel],
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Write each given market's own priority for one asset.
        Args:
            asset_id (int): ID of the owning asset.
            rows (Sequence[AssetSwitchModel]): The markets to write.
        Returns:
            return (Sequence[AssetSwitchModel]): The written markets.
        """
        stmt = self._bulk_update_stmt(
            rows, col(AssetSwitchModel.switch)
        ).where(col(AssetSwitchModel.asset_id) == asset_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_by_asset_and_id(
        self,
        asset_id: int,
        id: int,
        row: dict[str, Any],
    ) -> Optional[AssetSwitchModel]:
        """
        Desc: Patch one row of an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            id (int): ID of the row.
            row (dict[str, Any]): Column values to write.
        Returns:
            return (Optional[AssetSwitchModel]): Updated row or None.
        """
        stmt = (
            update(AssetSwitchModel)
            .where(col(AssetSwitchModel.id) == id)
            .where(col(AssetSwitchModel.asset_id) == asset_id)
            .values(**row)
            .returning(AssetSwitchModel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_asset_and_id(
        self,
        asset_id: int,
        id: int,
    ) -> Optional[AssetSwitchModel]:
        """
        Desc: Drop one row of an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            id (int): ID of the row.
        Returns:
            return (Optional[AssetSwitchModel]): Deleted row or None.
        """
        stmt = (
            delete(AssetSwitchModel)
            .where(col(AssetSwitchModel.id) == id)
            .where(col(AssetSwitchModel.asset_id) == asset_id)
            .returning(AssetSwitchModel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_asset_and_ids(
        self,
        asset_id: int,
        ids: Sequence[int],
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Drop several rows of an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            ids (Sequence[int]): IDs of the rows.
        Returns:
            return (Sequence[AssetSwitchModel]): The deleted rows.
        """
        stmt = (
            delete(AssetSwitchModel)
            .where(col(AssetSwitchModel.id).in_(ids))
            .where(col(AssetSwitchModel.asset_id) == asset_id)
            .returning(AssetSwitchModel)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_asset_id(
        self,
        asset_id: int,
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Get an asset's markets in pricing order.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (Sequence[AssetSwitchModel]): The markets, best first.
        """
        stmt = (
            select(AssetSwitchModel)
            .where(col(AssetSwitchModel.asset_id) == asset_id)
            .order_by(col(AssetSwitchModel.priority))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
