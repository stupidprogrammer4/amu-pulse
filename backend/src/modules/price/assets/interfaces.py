from typing import Protocol, Sequence

from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetUpdate,
)
from src.modules.price.assets.domain.models import AssetConfigModel, AssetModel


class IAssetConfigService(Protocol):
    async def create_default(self, asset_id: int) -> AssetConfigModel:
        """
        Desc: Create the default config of a newly created asset.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (AssetConfigModel): The created config.
        """
        ...

    async def update(
        self,
        asset_id: int,
        data: AssetConfigUpdate,
    ) -> AssetConfigModel:
        """
        Desc: Patch an asset's config.
        Args:
            asset_id (int): ID of the owning asset.
            data (AssetConfigUpdate): The fields to change.
        Returns:
            return (AssetConfigModel): The updated config.
        """
        ...

    async def get_by_asset_id(self, asset_id: int) -> AssetConfigModel:
        """
        Desc: Get an asset's config.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (AssetConfigModel): The found config.
        """
        ...

    async def get_all(self) -> Sequence[AssetConfigModel]:
        """
        Desc: Get every asset config.
        Returns:
            return (Sequence[AssetConfigModel]): All configs.
        """
        ...


class IAssetService(Protocol):
    async def create(self, data: AssetCreate) -> AssetModel:
        """
        Desc: Create an asset together with its default config.
        Args:
            data (AssetCreate): Validated payload to persist.
        Returns:
            return (AssetModel): The created asset.
        """
        ...

    async def update(self, id: int, data: AssetUpdate) -> AssetModel:
        """
        Desc: Patch an asset by id.
        Args:
            id (int): ID of the asset.
            data (AssetUpdate): The fields to change.
        Returns:
            return (AssetModel): The updated asset.
        """
        ...

    async def get_by_id(self, id: int) -> AssetModel:
        """
        Desc: Get an asset by id.
        Args:
            id (int): ID of the asset.
        Returns:
            return (AssetModel): The found asset.
        """
        ...

    async def get_all(self) -> Sequence[AssetModel]:
        """
        Desc: Get every asset.
        Returns:
            return (Sequence[AssetModel]): All assets.
        """
        ...

    async def get_all_with_config(self) -> Sequence[AssetModel]:
        """
        Desc: Get every asset with its config eagerly loaded.
        Returns:
            return (Sequence[AssetModel]): All assets, each carrying its
                config.
        """
        ...

    async def remove(self, id: int) -> AssetModel:
        """
        Desc: Delete an asset by id, its config cascading with it.
        Args:
            id (int): ID of the asset.
        Returns:
            return (AssetModel): The deleted asset.
        """
        ...
