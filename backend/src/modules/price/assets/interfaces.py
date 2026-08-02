from typing import Protocol, Sequence

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
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import (
    AssetConfigModel,
    AssetModel,
    AssetSwitchModel,
)


class IAssetConfigService(Protocol):
    async def create_default(
        self,
        asset_id: int,
        code: AssetCode,
    ) -> AssetConfigModel: ...

    async def update(
        self,
        asset_id: int,
        data: AssetConfigUpdate,
    ) -> AssetConfigModel: ...

    async def get_by_asset_id(self, asset_id: int) -> AssetConfigModel: ...

    async def get_all(self) -> Sequence[AssetConfigModel]: ...


class IAssetSwitchService(Protocol):
    async def create(
        self,
        asset_id: int,
        data: AssetSwitchCreate,
    ) -> AssetSwitchModel: ...

    async def batch_create(
        self,
        asset_id: int,
        data: AssetSwitchBatchCreate,
    ) -> Sequence[AssetSwitchModel]: ...

    async def update(
        self,
        asset_id: int,
        id: int,
        data: AssetSwitchUpdate,
    ) -> AssetSwitchModel: ...

    async def batch_update(
        self,
        asset_id: int,
        data: AssetSwitchBatchUpdate,
    ) -> Sequence[AssetSwitchModel]: ...

    async def set_priority(
        self,
        asset_id: int,
        data: AssetSwitchPriorityUpdate,
    ) -> Sequence[AssetSwitchModel]: ...

    async def remove(self, asset_id: int, id: int) -> AssetSwitchModel: ...

    async def batch_remove(
        self,
        asset_id: int,
        data: AssetSwitchBatchDelete,
    ) -> Sequence[AssetSwitchModel]: ...

    async def get_by_asset_id(
        self,
        asset_id: int,
    ) -> Sequence[AssetSwitchModel]: ...


class IAssetService(Protocol):
    async def create(self, data: AssetCreate) -> AssetModel: ...

    async def update(self, id: int, data: AssetUpdate) -> AssetModel: ...

    async def get_by_id(self, id: int) -> AssetModel: ...

    async def get_all(self) -> Sequence[AssetModel]: ...

    async def get_all_with_config(self) -> Sequence[AssetModel]: ...

    async def remove(self, id: int) -> AssetModel: ...
