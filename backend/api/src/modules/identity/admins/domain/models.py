from src.infra.postgres.models.base import BaseIDTimestampModel
from src.infra.postgres.types import BoolField, CharField


class AdminModel(BaseIDTimestampModel, table=True):
    username: str = CharField(55, unique=True)
    hashed_password: str = CharField(100)
    is_super_admin: bool = BoolField(default=lambda: False)
