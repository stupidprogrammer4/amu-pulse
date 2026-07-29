from datetime import datetime

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.price.assets.config.constants import (
    ASSET_ID_ENCRYPTION,
    AssetIDField,
)
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.sources.domain.enums import SourceSwitch


class AssetConfigOut(BaseOutput):
    asset_id: AssetIDField
    scheduler_on: bool
    scheduler_seconds: int
    switch: SourceSwitch
    agg_type: AggregationType
    created_at: datetime
    updated_at: datetime


class AssetOut(BaseIDOutput):
    __encryption__ = ASSET_ID_ENCRYPTION

    title: str
    code: AssetCode
    description: str | None
    created_at: datetime
    updated_at: datetime


class AssetWithConfigOut(AssetOut):
    config: AssetConfigOut
