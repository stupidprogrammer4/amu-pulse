from dishka import Provider, Scope, provide

from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)
from src.modules.price.assets.interfaces import (
    IAssetConfigService,
    IAssetService,
)


class AssetProvider(Provider):
    scope = Scope.REQUEST

    asset_repo = provide(AssetRepository)
    asset_config_repo = provide(AssetConfigRepository)
    asset_config_service = provide(
        AssetConfigService, provides=IAssetConfigService
    )
    asset_service = provide(AssetService, provides=IAssetService)
