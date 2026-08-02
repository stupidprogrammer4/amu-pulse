from dishka import Provider, Scope, provide

from src.modules.price.calculator.app.services import (
    BubbleCalculatorService,
    CalculatorService,
)
from src.modules.price.calculator.infra.cache import (
    AssetPriceCache,
    BubbleCache,
)
from src.modules.price.calculator.infra.readers import (
    AssetReader,
    BubbleReader,
    SourceReader,
    SwitchOrderReader,
    SymbolReader,
)
from src.modules.price.calculator.interfaces import (
    IBubbleCalculatorService,
    ICalculatorService,
)


class CalculatorProvider(Provider):
    scope = Scope.REQUEST

    # neither cache touches postgres, so neither pins a connection
    asset_price_cache = provide(AssetPriceCache, scope=Scope.APP)
    bubble_cache = provide(BubbleCache, scope=Scope.APP)
    symbol_reader = provide(SymbolReader)
    asset_reader = provide(AssetReader)
    bubble_reader = provide(BubbleReader)
    switch_order_reader = provide(SwitchOrderReader)
    source_reader = provide(SourceReader)
    calculator_service = provide(
        CalculatorService, provides=ICalculatorService
    )
    bubble_calculator_service = provide(
        BubbleCalculatorService, provides=IBubbleCalculatorService
    )
