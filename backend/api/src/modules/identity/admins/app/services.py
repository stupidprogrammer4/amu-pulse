import asyncio

from src.common.bases.results import PagedType
from src.common.bases.services import BaseIDService
from src.common.utils import crypto_utils
from src.core.config import Settings
from src.modules.identity.admins.config.constants import ADMIN_ID_ENCRYPTION
from src.modules.identity.admins.domain.dtos import (
    AdminCreate,
    AdminSearch,
    AdminUpdate,
)
from src.modules.identity.admins.domain.models import AdminModel
from src.modules.identity.admins.infra.repository import AdminRepository


class AdminService(BaseIDService[AdminModel]):
    def __init__(self, repo: AdminRepository, settings: Settings) -> None:
        """
        Desc: Build the service with its repository and the hashing secret.
        Args:
            repo (AdminRepository): The admin repository.
            settings (Settings): Read for crypto.password_salt, the pepper
                every password hash is derived with.
        """
        self.repo = repo
        self.pepper = settings.crypto.password_salt

    async def create(self, data: AdminCreate) -> AdminModel:
        """
        Desc: Create an admin, storing the password only as a hash.
        Args:
            data (AdminCreate): Validated payload to persist.
        Returns:
            return (AdminModel): The created admin.
        """
        row = data.to_row(exclude_unset=False)
        row["hashed_password"] = await self._hash(row.pop("password"))
        admin = await self.repo.create(AdminModel(**row))
        return admin

    async def update(self, id: int, data: AdminUpdate) -> AdminModel:
        """
        Desc: Patch an admin by id.
        Args:
            id (int): ID of the admin.
            data (AdminUpdate): The fields to change.
        Returns:
            return (AdminModel): The updated admin.
        """
        row = self._check_not_empty_dict(data.to_row())
        admin = await self.repo.update_by_id(id, row)
        admin = self._check_for_id_existence(id, admin)
        return admin

    async def set_username(self, id: int, username: str) -> AdminModel:
        """
        Desc: Change an admin's username.
        Args:
            id (int): ID of the admin.
            username (str): The username to move to.
        Returns:
            return (AdminModel): The updated admin.
        """
        admin = await self.repo.update_by_id(id, {"username": username})
        admin = self._check_for_id_existence(id, admin)
        return admin

    async def set_password(self, id: int, password: str) -> AdminModel:
        """
        Desc: Change an admin's password.
        Args:
            id (int): ID of the admin.
            password (str): The plain password to store the hash of.
        Returns:
            return (AdminModel): The updated admin.
        """
        hashed = await self._hash(password)
        admin = await self.repo.update_by_id(
            id, {"hashed_password": hashed}
        )
        admin = self._check_for_id_existence(id, admin)
        return admin

    async def verify_password(self, admin: AdminModel, password: str) -> bool:
        """
        Desc: Check a password against an admin's stored hash.
        Args:
            admin (AdminModel): The admin to check against.
            password (str): The plain password offered.
        Returns:
            return (bool): Whether the password is that admin's.
        """
        return await asyncio.to_thread(
            crypto_utils.verify_password,
            password,
            admin.hashed_password,
            pepper=self.pepper,
        )

    async def get_by_id(self, id: int) -> AdminModel:
        """
        Desc: Get an admin by id.
        Args:
            id (int): ID of the admin.
        Returns:
            return (AdminModel): The found admin.
        """
        admin = await self.repo.get_by_id(id)
        admin = self._check_for_id_existence(id, admin)
        return admin

    async def get_by_username(self, username: str) -> AdminModel:
        """
        Desc: Get an admin by username.
        Args:
            username (str): The username to look up.
        Returns:
            return (AdminModel): The found admin.
        """
        admin = await self.repo.get_by_username(username)
        admin = self._check_for_existence("username", username, admin)
        return admin

    async def get_paged(self, search: AdminSearch) -> PagedType[AdminModel]:
        """
        Desc: Get a filtered page of admins.
        Args:
            search (AdminSearch): Free text and paging.
        Returns:
            return (PagedType[AdminModel]): The page and the total count.
        """
        # an admin pastes a public id into the search box; match it as an id
        # too, not only as text
        id_match = None
        if search.q is not None and search.q.isdigit():
            id_match = ADMIN_ID_ENCRYPTION.try_decode(int(search.q))
        paged = await self.repo.get_paged(
            q=search.q,
            is_super_admin=search.is_super_admin,
            offset=(search.page - 1) * search.per_page,
            limit=search.per_page,
            id_match=id_match,
        )
        return paged

    async def remove(self, id: int) -> AdminModel:
        """
        Desc: Delete an admin by id.
        Args:
            id (int): ID of the admin.
        Returns:
            return (AdminModel): The deleted admin.
        """
        admin = await self.repo.delete_by_id(id)
        admin = self._check_for_id_existence(id, admin)
        return admin

    async def _hash(self, password: str) -> str:
        return await asyncio.to_thread(
            crypto_utils.hash_password, password, pepper=self.pepper
        )
