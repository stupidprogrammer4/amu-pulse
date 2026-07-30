from dataclasses import dataclass
from typing import Sequence

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetConfigModel
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceConfigModel
from src.modules.price.symbols.domain.enums import SymbolCode


@dataclass(frozen=True, slots=True)
class SourceContext:
    code: SourceCode
    id: int
    switch: SourceSwitch
    cfg: SourceConfigModel


@dataclass(frozen=True, slots=True)
class AssetRefContext:
    code: AssetCode
    id: int


@dataclass(frozen=True, slots=True)
class SymbolRefContext:
    code: SymbolCode
    id: int


@dataclass(frozen=True, slots=True)
class AssetContext:
    code: AssetCode
    id: int
    cfg: AssetConfigModel


@dataclass(frozen=True, slots=True)
class CFGContext:
    sources: Sequence[SourceContext]
    symbols: Sequence[SymbolRefContext]
    assets: Sequence[AssetRefContext]
