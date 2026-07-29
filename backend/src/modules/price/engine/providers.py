from dishka import Provider, Scope, provide

from src.modules.price.engine.app.services import PricingEngineService
from src.modules.price.engine.infra.readers import AssetReader, SourceReader
from src.modules.price.engine.interfaces import IPricingEngineService


class EngineProvider(Provider):
    scope = Scope.REQUEST

    asset_reader = provide(AssetReader)
    source_reader = provide(SourceReader)
    pricing_engine_service = provide(
        PricingEngineService,
        provides=IPricingEngineService
    )
