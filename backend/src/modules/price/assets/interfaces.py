from typing import Protocol, Sequence

from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetUpdate,
)
from src.modules.price.assets.domain.models import AssetConfigModel, AssetModel


class IAssetConfigService(Protocol):
    async def create_default(self, asset_id: int) -> AssetConfigModel: ...

    async def update(
        self,
        asset_id: int,
        data: AssetConfigUpdate,
    ) -> AssetConfigModel: ...

    async def get_by_asset_id(self, asset_id: int) -> AssetConfigModel: ...

    async def get_all(self) -> Sequence[AssetConfigModel]: ...


class IAssetService(Protocol):
    async def create(self, data: AssetCreate) -> AssetModel: ...

    async def update(self, id: int, data: AssetUpdate) -> AssetModel: ...

    async def get_by_id(self, id: int) -> AssetModel: ...

    async def get_all(self) -> Sequence[AssetModel]: ...

    async def get_all_with_config(self) -> Sequence[AssetModel]: ...

    async def remove(self, id: int) -> AssetModel: ...
