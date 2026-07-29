from typing import Annotated

from pydantic import Field

from src.common.bases.dtos import BaseDTO
from src.common.types import ContentType, StrType
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.sources.domain.enums import SourceSwitch

# the polling period of an asset's scheduler, in whole seconds
SecondType = Annotated[int, Field(ge=20, le=300)]


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
    switch: SourceSwitch | None = None
    agg_type: AggregationType | None = None
