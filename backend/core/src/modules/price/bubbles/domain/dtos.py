from typing import Annotated

from pydantic import Field

from src.common.bases.dtos import BaseDTO
from src.common.types import ContentType, StrType
from src.modules.price.assets.domain.enums import AggregationType, AssetCode

# the polling period of a bubble's scheduler, in whole seconds
SecondType = Annotated[int, Field(ge=20, le=300)]


class BubbleCreate(BaseDTO):
    title: StrType
    code: AssetCode
    description: ContentType | None = None


class BubbleUpdate(BaseDTO):
    title: StrType | None = None
    description: ContentType | None = None


class BubbleConfigUpdate(BaseDTO):
    scheduler_on: bool | None = None
    scheduler_seconds: SecondType | None = None
    agg_type: AggregationType | None = None
