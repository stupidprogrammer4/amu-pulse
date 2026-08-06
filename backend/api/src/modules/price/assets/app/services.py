from typing import Sequence

from src.common.bases.services import BaseIDService, BaseService
from src.common.errors.exceptions import ValidationException
from src.modules.price.assets.config import resources
from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetSwitchBatchCreate,
    AssetSwitchBatchDelete,
    AssetSwitchBatchUpdate,
    AssetSwitchCreate,
    AssetSwitchPriorityUpdate,
    AssetSwitchUpdate,
    AssetUpdate,
)
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.domain.models import (
    AssetConfigModel,
    AssetModel,
    AssetSwitchModel,
)
from src.modules.price.assets.domain.schemas import (
    AssetMeta,
    AssetMetaOut,
)
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.assets.interfaces import (
    IAssetConfigService,
    IAssetService,
)
from src.modules.price.calculator.interfaces import ISchedulerService
from src.modules.price.sources.domain.enums import SourceSwitch


class AssetConfigService(BaseService[AssetConfigModel]):
    default_scheduler_on = False
    default_scheduler_seconds = 60
    default_agg_type = AggregationType.MEDIAN
    usd_scheduler_on = True
    usd_scheduler_seconds = 20

    def __init__(
        self,
        repo: AssetConfigRepository,
        asset_repo: AssetRepository,
        scheduler: ISchedulerService,
    ) -> None:
        self.repo = repo
        self.scheduler = scheduler
        self.asset_repo = asset_repo

    async def _check_for_usd(
        self,
        asset_id: int,
    ):
        """
        Desc: Refuse to change the config of the USD asset.
        Args:
            asset_id (int): ID of the owning asset.
        """
        code = await self.asset_repo.get_code_by_id(asset_id)
        if code == AssetCode.USD:
            raise ValidationException(
                message="The USD asset is not configurable",
                message_code=resources.ASSET_CONFIG_USD,
                loc=["path", "asset_id"],
                input=asset_id,
            )

    async def create_default(
        self,
        asset_id: int,
        code: AssetCode,
    ) -> AssetConfigModel:
        """
        Desc: Create the default config of a newly created asset.
        Args:
            asset_id (int): ID of the owning asset.
            code (AssetCode): Code of the owning asset.
        Returns:
            return (AssetConfigModel): The created config.
        """
        scheduler_on = self.default_scheduler_on
        scheduler_seconds = self.default_scheduler_seconds
        if code == AssetCode.USD:
            scheduler_on = self.usd_scheduler_on
            scheduler_seconds = self.usd_scheduler_seconds
        config = await self.repo.create(
            AssetConfigModel(
                asset_id=asset_id,
                scheduler_on=scheduler_on,
                scheduler_seconds=scheduler_seconds,
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
        if data.scheduler_on is not None or data.scheduler_seconds is not None:
            await self._check_for_usd(asset_id)
            await self.scheduler.sync(
                asset_id,
                config.scheduler_on,
                config.scheduler_seconds,
            )
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


class AssetSwitchService(BaseIDService[AssetSwitchModel]):
    def __init__(self, repo: AssetSwitchRepository) -> None:
        self.repo = repo

    def _check_no_repeat(
        self,
        switches: Sequence[SourceSwitch],
        loc: str,
    ) -> Sequence[SourceSwitch]:
        """
        Desc: Refuse an order that names the same market twice.
        Args:
            switches (Sequence[SourceSwitch]): The markets given.
            loc (str): The input field the markets came from.
        Returns:
            return (Sequence[SourceSwitch]): The same markets.
        """
        if len(set(switches)) != len(switches):
            raise ValidationException(
                message="A market may appear once in the order",
                message_code=resources.ASSET_SWITCH_DUPLICATED,
                loc=["body", loc],
                input=[switch.value for switch in switches],
            )
        return switches

    async def create(
        self,
        asset_id: int,
        data: AssetSwitchCreate,
    ) -> AssetSwitchModel:
        """
        Desc: Add one market to an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            data (AssetSwitchCreate): The market and its level.
        Returns:
            return (AssetSwitchModel): The created row.
        """
        row = await self.repo.create(
            AssetSwitchModel(
                asset_id=asset_id,
                switch=data.switch,
                priority=data.priority,
            )
        )
        return row

    async def batch_create(
        self,
        asset_id: int,
        data: AssetSwitchBatchCreate,
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Give an asset the markets it is priced from.
        Args:
            asset_id (int): ID of the owning asset.
            data (AssetSwitchBatchCreate): The markets and their levels.
        Returns:
            return (Sequence[AssetSwitchModel]): The created rows.
        """
        items = self._check_not_empty_list(data.items)
        self._check_no_repeat([item.switch for item in items], "items")
        rows = await self.repo.bulk_create(
            [
                AssetSwitchModel(
                    asset_id=asset_id,
                    switch=item.switch,
                    priority=item.priority,
                )
                for item in items
            ]
        )
        return rows

    async def update(
        self,
        asset_id: int,
        id: int,
        data: AssetSwitchUpdate,
    ) -> AssetSwitchModel:
        """
        Desc: Patch one row of an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            id (int): ID of the row.
            data (AssetSwitchUpdate): The fields to change.
        Returns:
            return (AssetSwitchModel): The updated row.
        """
        patch = self._check_not_empty_dict(data.to_row())
        row = await self.repo.update_by_asset_and_id(asset_id, id, patch)
        row = self._check_for_id_existence(id, row)
        return row

    async def batch_update(
        self,
        asset_id: int,
        data: AssetSwitchBatchUpdate,
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Give each market of an asset its own priority level.
        Args:
            asset_id (int): ID of the owning asset.
            data (AssetSwitchBatchUpdate): The markets and their levels.
        Returns:
            return (Sequence[AssetSwitchModel]): The written rows.
        """
        items = self._check_not_empty_list(data.items)
        self._check_no_repeat([item.switch for item in items], "items")
        rows = await self.repo.bulk_update(
            asset_id,
            [
                AssetSwitchModel(
                    asset_id=asset_id,
                    switch=item.switch,
                    priority=item.priority,
                )
                for item in items
            ],
        )
        return rows

    async def set_priority(
        self,
        asset_id: int,
        data: AssetSwitchPriorityUpdate,
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Move several markets of an asset onto one priority level.
        Args:
            asset_id (int): ID of the owning asset.
            data (AssetSwitchPriorityUpdate): The level and its markets.
        Returns:
            return (Sequence[AssetSwitchModel]): The moved rows.
        """
        switches = self._check_not_empty_list(data.switches)
        self._check_no_repeat(switches, "switches")
        rows = await self.repo.bulk_update(
            asset_id,
            [
                AssetSwitchModel(
                    asset_id=asset_id,
                    switch=switch,
                    priority=data.priority,
                )
                for switch in switches
            ],
        )
        return rows

    async def remove(self, asset_id: int, id: int) -> AssetSwitchModel:
        """
        Desc: Drop one market from an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            id (int): ID of the row.
        Returns:
            return (AssetSwitchModel): The deleted row.
        """
        row = await self.repo.delete_by_asset_and_id(asset_id, id)
        row = self._check_for_id_existence(id, row)
        return row

    async def batch_remove(
        self,
        asset_id: int,
        data: AssetSwitchBatchDelete,
    ) -> Sequence[AssetSwitchModel]:
        """
        Desc: Drop several markets from an asset's pricing order.
        Args:
            asset_id (int): ID of the owning asset.
            data (AssetSwitchBatchDelete): IDs of the rows to drop.
        Returns:
            return (Sequence[AssetSwitchModel]): The deleted rows.
        """
        ids = self._check_not_empty_list(data.ids)
        rows = await self.repo.delete_by_asset_and_ids(asset_id, ids)
        return rows

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
        rows = await self.repo.get_by_asset_id(asset_id)
        return rows


class AssetService(BaseIDService[AssetModel]):
    def __init__(
        self,
        repo: AssetRepository,
        configs: IAssetConfigService,
    ) -> None:
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
        await self.configs.create_default(asset.id, data.code)
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

    async def get_by_ids(
        self,
        ids: list[int],
    ) -> Sequence[AssetModel]:
        """
        Desc: Get the assets the given ids belong to.
        Args:
            ids (list[int]): IDs of the assets to read.
        Returns:
            return (Sequence[AssetModel]): The assets that exist.
        """
        assets = await self.repo.get_by_ids(ids)
        return assets

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


class AssetMetaService:
    def __init__(self, assets: IAssetService) -> None:
        self.assets = assets

    async def build(self, asset_ids: Sequence[int]) -> AssetMeta:
        """
        Desc: Name the assets the given ids belong to.
        Args:
            asset_ids (Sequence[int]): IDs of the assets to name.
        Returns:
            return (AssetMeta): One entry per asset that exists.
        """
        assets = await self.assets.get_by_ids(list(asset_ids))
        return AssetMeta(assets=AssetMetaOut.from_objs(assets))
