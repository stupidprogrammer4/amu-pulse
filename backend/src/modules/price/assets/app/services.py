from typing import Sequence

from src.common.bases.services import BaseIDService, BaseService
from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetUpdate,
)
from src.modules.price.assets.domain.enums import AggregationType
from src.modules.price.assets.domain.models import AssetConfigModel, AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.assets.interfaces import IAssetConfigService
from src.modules.price.sources.domain.enums import SourceSwitch


class AssetConfigService(BaseService[AssetConfigModel]):
    # what a freshly created asset polls with until an admin tunes it
    default_scheduler_on = True
    default_scheduler_seconds = 60
    default_switch = SourceSwitch.IRAN_MARKET
    default_agg_type = AggregationType.MEDIAN

    def __init__(self, repo: AssetConfigRepository) -> None:
        """
        Desc: Build the service with its repository.
        Args:
            repo (AssetConfigRepository): The asset config repository.
        """
        self.repo = repo

    async def create_default(self, asset_id: int) -> AssetConfigModel:
        """
        Desc: Create the default config of a newly created asset.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (AssetConfigModel): The created config.
        """
        config = await self.repo.create(
            AssetConfigModel(
                asset_id=asset_id,
                scheduler_on=self.default_scheduler_on,
                scheduler_seconds=self.default_scheduler_seconds,
                switch=self.default_switch,
                agg_type=self.default_agg_type,
            )
        )
        return config

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
        row = self._check_not_empty_dict(data.to_row())
        config = await self.repo.update_by_asset_id(asset_id, row)
        config = self._check_for_existence("asset_id", asset_id, config)
        return config

    async def get_by_asset_id(self, asset_id: int) -> AssetConfigModel:
        """
        Desc: Get an asset's config.
        Args:
            asset_id (int): ID of the owning asset.
        Returns:
            return (AssetConfigModel): The found config.
        """
        config = await self.repo.get_by_asset_id(asset_id)
        config = self._check_for_existence("asset_id", asset_id, config)
        return config

    async def get_all(self) -> Sequence[AssetConfigModel]:
        """
        Desc: Get every asset config.
        Returns:
            return (Sequence[AssetConfigModel]): All configs.
        """
        configs = await self.repo.get_all()
        return configs


class AssetService(BaseIDService[AssetModel]):
    def __init__(
        self,
        repo: AssetRepository,
        configs: IAssetConfigService,
    ) -> None:
        """
        Desc: Build the service with its repository and the config service.
        Args:
            repo (AssetRepository): The asset repository.
            configs (IAssetConfigService): The asset config service.
        """
        self.repo = repo
        self.configs = configs

    async def create(self, data: AssetCreate) -> AssetModel:
        """
        Desc: Create an asset together with its default config.
        Args:
            data (AssetCreate): Validated payload to persist.
        Returns:
            return (AssetModel): The created asset.
        """
        asset = await self.repo.create(
            AssetModel(**data.to_row(exclude_unset=False))
        )
        await self.configs.create_default(asset.id)
        return asset

    async def update(self, id: int, data: AssetUpdate) -> AssetModel:
        """
        Desc: Patch an asset by id.
        Args:
            id (int): ID of the asset.
            data (AssetUpdate): The fields to change.
        Returns:
            return (AssetModel): The updated asset.
        """
        row = self._check_not_empty_dict(data.to_row())
        asset = await self.repo.update_by_id(id, row)
        asset = self._check_for_id_existence(id, asset)
        return asset

    async def get_by_id(self, id: int) -> AssetModel:
        """
        Desc: Get an asset by id.
        Args:
            id (int): ID of the asset.
        Returns:
            return (AssetModel): The found asset.
        """
        asset = await self.repo.get_by_id(id)
        asset = self._check_for_id_existence(id, asset)
        return asset

    async def get_all(self) -> Sequence[AssetModel]:
        """
        Desc: Get every asset.
        Returns:
            return (Sequence[AssetModel]): All assets.
        """
        assets = await self.repo.get_all()
        return assets

    async def get_all_with_config(self) -> Sequence[AssetModel]:
        """
        Desc: Get every asset with its config eagerly loaded.
        Returns:
            return (Sequence[AssetModel]): All assets, each carrying its
                config.
        """
        assets = await self.repo.get_all_with_config()
        return assets

    async def remove(self, id: int) -> AssetModel:
        """
        Desc: Delete an asset by id, its config cascading with it.
        Args:
            id (int): ID of the asset.
        Returns:
            return (AssetModel): The deleted asset.
        """
        asset = await self.repo.delete_by_id(id)
        asset = self._check_for_id_existence(id, asset)
        return asset
