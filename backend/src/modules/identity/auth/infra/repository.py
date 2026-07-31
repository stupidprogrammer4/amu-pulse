from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlmodel import col, select

from src.common.utils import date_utils
from src.infra.postgres.repository.base import PGIDRepository
from src.modules.identity.auth.domain.models import (
    LoginLogModel,
    RefreshTokenModel,
    RoleModel,
    UserModel,
)


class RoleRepository(PGIDRepository[RoleModel]):
    async def get_by_code(self, code: str) -> Optional[RoleModel]:
        """
        Desc: Get a role by its code.
        Args:
            code (str): The role's unique code (e.g. "admin").
        Returns:
            return (Optional[RoleModel]): Found role or None.
        """
        stmt = select(RoleModel).where(col(RoleModel.code) == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class UserRepository(PGIDRepository[UserModel]):
    async def get_by_mobile(
        self,
        mobile: str,
    ) -> Optional[UserModel]:
        """
        Desc: Get a user by mobile number, with its role loaded.
        Args:
            mobile (str): The normalized 09xxxxxxxxx mobile number.
        Returns:
            return (Optional[UserModel]): Found user or None.
        """
        stmt = (
            select(UserModel)
            .options(joinedload(UserModel.role, innerjoin=True))
            .where(col(UserModel.mobile) == mobile)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_id_with_role(self, id: int) -> Optional[UserModel]:
        """
        Desc: Get a user by id, with its role loaded.
        Args:
            id (int): ID of the user.
        Returns:
            return (Optional[UserModel]): Found user or None.
        """
        stmt = (
            select(UserModel)
            .options(joinedload(UserModel.role, innerjoin=True))
            .where(col(UserModel.id) == id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()


class RefreshTokenRepository(PGIDRepository[RefreshTokenModel]):
    async def get_active_by_hash(
        self,
        token_hash: str,
    ) -> Optional[RefreshTokenModel]:
        """
        Desc: Get a non-revoked refresh token row by its hash.
        Args:
            token_hash (str): sha256 hex digest of the raw token.
        Returns:
            return (Optional[RefreshTokenModel]): Found row or None.
        """
        stmt = select(RefreshTokenModel).where(
            col(RefreshTokenModel.token_hash) == token_hash,
            col(RefreshTokenModel.revoked_at).is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_by_id(self, id: int) -> Optional[RefreshTokenModel]:
        """
        Desc: Mark a refresh token row as revoked.
        Args:
            id (int): ID of the refresh token row.
        Returns:
            return (Optional[RefreshTokenModel]): Updated row or None.
        """
        stmt = (
            update(RefreshTokenModel)
            .where(col(RefreshTokenModel.id) == id)
            .values(revoked_at=date_utils.utc_now())
            .returning(RefreshTokenModel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class LoginLogRepository(PGIDRepository[LoginLogModel]):
    pass