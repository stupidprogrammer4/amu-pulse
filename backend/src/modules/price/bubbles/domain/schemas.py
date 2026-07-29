from datetime import datetime

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.bubbles.config.constants import (
    BUBBLE_ID_ENCRYPTION,
    BubbleIDField,
)


class BubbleConfigOut(BaseOutput):
    bubble_id: BubbleIDField
    scheduler_on: bool
    scheduler_seconds: int
    agg_type: AggregationType
    created_at: datetime
    updated_at: datetime


class BubbleOut(BaseIDOutput):
    __encryption__ = BUBBLE_ID_ENCRYPTION

    title: str
    code: AssetCode
    description: str | None
    created_at: datetime
    updated_at: datetime


class BubbleWithConfigOut(BubbleOut):
    config: BubbleConfigOut | None = None
