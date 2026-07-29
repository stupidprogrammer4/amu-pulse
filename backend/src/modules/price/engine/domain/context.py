from dataclasses import dataclass
from typing import Sequence

from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetConfigModel
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceConfigModel


@dataclass
class SourceContext:
    code: SourceCode
    id: int
    swith: SourceSwitch
    cfg: SourceConfigModel

@dataclass
class AssetContext:
    code: AssetCode
    id: int
    cfg: AssetConfigModel

@dataclass
class ALLCFGContext:
    sources: Sequence[SourceContext]
    assets: Sequence[AssetContext]

@dataclass
class CFGContext:
    sources: Sequence[SourceContext]
    asset: AssetContext

