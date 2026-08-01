from dishka import Provider, Scope, provide

from src.modules.price.calculator.app.services import BubbleCalculatorService
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)
from src.modules.price.calculator.infra.readers import (
    AssetReader,
    BubbleReader,
    SwitchOrderReader,
    SymbolReader,
)
from src.modules.price.calculator.interfaces import IBubbleCalculatorService


class CalculatorProvider(Provider):
    scope = Scope.REQUEST

    # neither cache touches postgres, so neither pins a connection
    asset_price_cache = provide(AssetPriceCache, scope=Scope.APP)
    bubble_cache = provide(BubbleCache, scope=Scope.APP)
    symbol_reader = provide(SymbolReader)
    asset_reader = provide(AssetReader)
    bubble_reader = provide(BubbleReader)
    switch_order_reader = provide(SwitchOrderReader)
    bubble_calculator_service = provide(
        BubbleCalculatorService, provides=IBubbleCalculatorService
    )
