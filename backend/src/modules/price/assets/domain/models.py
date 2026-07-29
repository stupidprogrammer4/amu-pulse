from typing import Optional

from sqlalchemy.orm import Mapped, declared_attr
from sqlmodel import Relationship

from src.infra.postgres.models.base import (
    BaseIDTimestampModel,
    BaseTimestampModel,
)
from src.infra.postgres.types import (
    BoolField,
    CharField,
    ForeignKeyField,
    IntField,
    TextField,
)
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.sources.domain.enums import SourceSwitch


class AssetModel(BaseIDTimestampModel, table=True):
    title: str = CharField(55)
    code: AssetCode = CharField(55, unique=True)
    description: str | None = TextField(nullable=True)

    config: Mapped[Optional["AssetConfigModel"]] = Relationship(
        back_populates="asset",
        sa_relationship_kwargs={"uselist": False},
    )


class AssetConfigModel(BaseTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_asset_configs"

    asset_id: int = ForeignKeyField(
        "tbl_assets.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    scheduler_on: bool = BoolField()
    scheduler_seconds: int = IntField()
    switch: SourceSwitch = CharField(55)
    agg_type: AggregationType = CharField(55)

    asset: Optional[AssetModel] = Relationship(back_populates="config")
