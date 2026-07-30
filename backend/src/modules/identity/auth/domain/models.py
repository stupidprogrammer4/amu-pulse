from datetime import datetime

from sqlalchemy.orm import Mapped, declared_attr
from sqlmodel import Relationship

from src.infra.postgres.models.base import BaseIDTimestampModel
from src.infra.postgres.types import (
    BoolField,
    CharField,
    ForeignKeyField,
    IntField,
    JSONBField,
    TimestampField,
)


class RoleModel(BaseIDTimestampModel, table=True):
    code: str = CharField(20, unique=True)
    title: str = CharField(55)
    permissions: list[str] = JSONBField()


class UserModel(BaseIDTimestampModel, table=True):
    mobile: str = CharField(11, unique=True)
    password_hash: str = CharField(255)
    full_name: str | None = CharField(100, nullable=True)
    is_active: bool = BoolField(default=True)
    role_id: int = ForeignKeyField("tbl_roles.id")
    last_login_at: datetime | None = TimestampField(nullable=True)
    last_login_ip: str | None = CharField(45, nullable=True)
    failed_login_attempts: int = IntField(default=0)
    locked_until: datetime | None = TimestampField(nullable=True)

    role: Mapped[RoleModel] = Relationship()


class RefreshTokenModel(BaseIDTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_refresh_tokens"

    user_id: int = ForeignKeyField("tbl_users.id", ondelete="CASCADE")
    # sha256 hex digest of the raw token — the raw JWT is never stored
    token_hash: str = CharField(64, unique=True)
    expires_at: datetime = TimestampField()
    revoked_at: datetime | None = TimestampField(nullable=True)
    device: str | None = CharField(255, nullable=True)
    ip: str | None = CharField(45, nullable=True)


class LoginLogModel(BaseIDTimestampModel, table=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "tbl_login_logs"

    # null when the mobile itself didn't match any user
    user_id: int | None = ForeignKeyField(
        "tbl_users.id", ondelete="SET NULL", nullable=True
    )
    mobile: str = CharField(11)
    ip: str | None = CharField(45, nullable=True)
    device: str | None = CharField(255, nullable=True)
    success: bool = BoolField()