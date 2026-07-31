from typing import Protocol

from src.modules.identity.auth.domain.dtos import (
    TokenRefresh,
    UserLogin,
    UserRegister,
)
from src.modules.identity.auth.domain.models import UserModel
from src.modules.identity.auth.domain.results import AuthResult


class IAuthService(Protocol):
    async def register(
        self, data: UserRegister, ip: str | None, device: str | None
    ) -> AuthResult: ...

    async def login(
        self, data: UserLogin, ip: str | None, device: str | None
    ) -> AuthResult: ...

    async def refresh(
        self, data: TokenRefresh, ip: str | None, device: str | None
    ) -> AuthResult: ...

    async def logout(self, data: TokenRefresh) -> None: ...

    async def get_by_id(self, id: int) -> UserModel: ...