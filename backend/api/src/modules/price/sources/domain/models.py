from typing import Optional

from sqlalchemy.orm import Mapped, declared_attr
from sqlmodel import Relationship

from src.infra.postgres.models.base import (
    BaseIDTimestampModel,
    BaseTimestampModel,
)
from src.infra.postgres.types import (
    CharField,
    ForeignKeyField,
    IntField,
    JSONBField,
)
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.errors import SourceErrorInfo


class SourceModel(BaseIDTimestampModel, table=True):
    title: str = CharField(55)
    code: SourceCode = CharField(55, unique=True)
    website_url: str = CharField(255)
    icon_url: str = CharField(255)
    primary_color: str = CharField(16)
    source_type: SourceSwitch = CharField(55)
    error: SourceErrorInfo | None = JSONBField(nullable=True)

    config: Mapped[Optional["SourceConfigModel"]] = Relationship(
        back_populates="source",
        sa_relationship_kwargs={"uselist": False},
    )


class SourceConfigModel(BaseTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_source_configs"

    source_id: int = ForeignKeyField(
        "tbl_sources.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    timeout: int = IntField()
    headers_credentials: dict[str, str] | None = JSONBField(nullable=True)
    auth_credentials: dict[str, str] | None = JSONBField(nullable=True)

    source: Mapped[Optional[SourceModel]] = Relationship(
        back_populates="config"
    )
