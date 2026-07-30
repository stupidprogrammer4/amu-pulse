from dishka import Provider, Scope, provide

from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
    AssetSwitchService,
)
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.assets.interfaces import (
    IAssetConfigService,
    IAssetService,
    IAssetSwitchService,
)


class AssetProvider(Provider):
    scope = Scope.REQUEST

    asset_repo = provide(AssetRepository)
    asset_config_repo = provide(AssetConfigRepository)
    asset_switch_repo = provide(AssetSwitchRepository)
    asset_config_service = provide(
        AssetConfigService, provides=IAssetConfigService
    )
    asset_switch_service = provide(
        AssetSwitchService, provides=IAssetSwitchService
    )
    asset_service = provide(AssetService, provides=IAssetService)
