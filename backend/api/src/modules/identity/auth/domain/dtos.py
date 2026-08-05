from src.common.bases.dtos import BaseDTO
from src.modules.identity.admins.domain.dtos import UsernameType


class AdminLoginIn(BaseDTO):
    username: UsernameType
    # plain str, not PasswordType: a login must accept whatever is typed and
    # answer "wrong credentials", never 422 on a password that is too short
    password: str


class RefreshIn(BaseDTO):
    refresh_token: str
