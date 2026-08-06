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


class BubbleModel(BaseIDTimestampModel, table=True):
    code: AssetCode = CharField(55, unique=True)
    title: str = CharField(55)
    description: str | None = TextField(nullable=True)

    config: Mapped[Optional["BubbleConfigModel"]] = Relationship(
        back_populates="bubble",
        sa_relationship_kwargs={"uselist": False},
    )


class BubbleConfigModel(BaseTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_bubble_configs"

    bubble_id: int = ForeignKeyField(
        "tbl_bubbles.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    scheduler_on: bool = BoolField()
    scheduler_seconds: int = IntField()
    agg_type: AggregationType = CharField(55)

    bubble: Optional[BubbleModel] = Relationship(back_populates="config")
