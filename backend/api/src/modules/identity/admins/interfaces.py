from typing import Protocol

from src.common.bases.results import PagedType
from src.modules.identity.admins.domain.dtos import (
    AdminCreate,
    AdminSearch,
    AdminUpdate,
)
from src.modules.identity.admins.domain.models import AdminModel


class IAdminService(Protocol):
    async def create(self, data: AdminCreate) -> AdminModel: ...

    async def update(self, id: int, data: AdminUpdate) -> AdminModel: ...

    async def set_username(self, id: int, username: str) -> AdminModel: ...

    async def set_password(self, id: int, password: str) -> AdminModel: ...

    async def verify_password(
        self, admin: AdminModel, password: str
    ) -> bool: ...

    async def get_by_id(self, id: int) -> AdminModel: ...

    async def remove(self, id: int) -> AdminModel: ...

    async def get_by_username(self, username: str) -> AdminModel: ...

    async def get_paged(
        self,
        search: AdminSearch,
    ) -> PagedType[AdminModel]: ...
