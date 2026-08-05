from datetime import datetime

from pydantic import BaseModel

from src.modules.price.engine.domain.results import PriceResult


class AssetPriceResult(PriceResult):
    asset_id: int


class BubbleResult(BaseModel):
    asset_id: int
    amount: int
    priced_at: datetime
