from datetime import datetime

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.price.assets.config.constants import (
    ASSET_ID_ENCRYPTION,
    ASSET_SWITCH_ID_ENCRYPTION,
    AssetIDField,
)
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.sources.domain.enums import SourceSwitch


class AssetConfigOut(BaseOutput):
    asset_id: AssetIDField
    scheduler_on: bool
    scheduler_seconds: int
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


class AssetSwitchOut(BaseIDOutput):
    __encryption__ = ASSET_SWITCH_ID_ENCRYPTION

    asset_id: AssetIDField
    switch: SourceSwitch
    priority: int
    created_at: datetime
    updated_at: datetime
