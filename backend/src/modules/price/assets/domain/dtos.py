from typing import Annotated

from pydantic import Field

from src.common.bases.dtos import BaseDTO
from src.common.types import ContentType, StrType
from src.modules.price.assets.config.constants import AssetSwitchIDInput
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.sources.domain.enums import SourceSwitch

# the polling period of an asset's scheduler, in whole seconds
SecondType = Annotated[int, Field(ge=20, le=300)]

# where a market sits in the pricing order; lower comes first
PriorityType = Annotated[int, Field(ge=0, le=100)]


class AssetCreate(BaseDTO):
    title: StrType
    code: AssetCode
    description: ContentType | None = None


class AssetUpdate(BaseDTO):
    title: StrType | None = None
    description: ContentType | None = None


class AssetConfigUpdate(BaseDTO):
    scheduler_on: bool | None = None
    scheduler_seconds: SecondType | None = None
    agg_type: AggregationType | None = None


class AssetSwitchCreate(BaseDTO):
    switch: SourceSwitch
    priority: PriorityType


class AssetSwitchUpdate(BaseDTO):
    switch: SourceSwitch | None = None
    priority: PriorityType | None = None


class AssetSwitchBatchCreate(BaseDTO):
    items: list[AssetSwitchCreate]


class AssetSwitchBatchUpdate(BaseDTO):
    items: list[AssetSwitchCreate]


class AssetSwitchBatchDelete(BaseDTO):
    ids: list[AssetSwitchIDInput]


class AssetSwitchPriorityUpdate(BaseDTO):
    priority: PriorityType
    switches: list[SourceSwitch]
