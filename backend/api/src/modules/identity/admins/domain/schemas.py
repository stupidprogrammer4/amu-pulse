from datetime import datetime

from src.common.bases.schemas import BaseIDOutput
from src.modules.identity.admins.config.constants import ADMIN_ID_ENCRYPTION


class AdminOut(BaseIDOutput):
    __encryption__ = ADMIN_ID_ENCRYPTION

    username: str
    is_super_admin: bool
    created_at: datetime
    updated_at: datetime
