from datetime import datetime

from src.common.bases.schemas import (
    BaseIDOutput,
    BaseMeta,
    BaseOutput,
)
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
    primary_color: str
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


class AssetPriceOut(BaseOutput):
    asset_id: AssetIDField
    buy_price: int
    sell_price: int
    price: int
    buy_spread: int
    sell_spread: int
    buy_spread_rate: float
    sell_spread_rate: float
    priced_at: datetime


class RepriceOut(BaseOutput):
    task_id: str


class AssetMetaOut(BaseOutput):
    id: AssetIDField
    code: AssetCode
    title: str
    primary_color: str


class AssetMeta(BaseMeta):
    assets: list[AssetMetaOut]
