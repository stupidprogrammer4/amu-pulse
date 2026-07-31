from datetime import datetime

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.identity.auth.config.constants import USER_ID_ENCRYPTION


class RoleOut(BaseIDOutput):
    code: str
    title: str


class UserOut(BaseIDOutput):
    __encryption__ = USER_ID_ENCRYPTION

    mobile: str
    full_name: str | None
    is_active: bool
    role: RoleOut
    last_login_at: datetime | None
    created_at: datetime


class AuthOut(BaseOutput):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"