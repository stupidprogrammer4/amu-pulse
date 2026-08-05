from typing import Protocol

from src.modules.identity.auth.domain.results import AdminAuthType


class IAdminAuthService(Protocol):
    async def login(self, username: str, password: str) -> AdminAuthType: ...

    async def refresh(self, refresh_token: str) -> AdminAuthType: ...
