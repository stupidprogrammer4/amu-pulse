from dataclasses import dataclass

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetConfigModel
from src.modules.price.bubbles.domain.models import BubbleConfigModel
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.symbols.domain.enums import SymbolCode


@dataclass
class SymbolContext:
    id: int
    code: AssetCode
    symbol: SymbolCode
    asset_id: int


@dataclass
class AssetContext:
    code: AssetCode
    asset_id: int
    config: AssetConfigModel


@dataclass
class BubbleContext:
    code: AssetCode
    bubble_id: int
    config: BubbleConfigModel


@dataclass
class SwitchOrderContext:
    code: AssetCode
    asset_id: int
    switch: SourceSwitch
    order: int
