from src.common.bases.dtos import BaseDTO
from src.modules.identity.admins.domain.dtos import UsernameType


class AdminLoginIn(BaseDTO):
    username: UsernameType
    password: str


class RefreshIn(BaseDTO):
    refresh_token: str
