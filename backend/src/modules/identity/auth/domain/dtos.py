from src.common.bases.dtos import BaseDTO
from src.common.types import LStrType, MobileType, PasswordType


class UserRegister(BaseDTO):
    mobile: MobileType
    password: PasswordType
    full_name: LStrType | None = None


class UserLogin(BaseDTO):
    mobile: MobileType
    password: PasswordType


class TokenRefresh(BaseDTO):
    refresh_token: str