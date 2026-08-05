from sqlalchemy import ColumnElement
from sqlmodel import col, select

from src.common.bases.results import PagedType
from src.infra.postgres.repository.base import PGIDRepository
from src.modules.identity.admins.domain.models import AdminModel


class AdminRepository(PGIDRepository[AdminModel]):
    async def get_by_username(self, username: str) -> AdminModel | None:
        """
        Desc: Get the admin holding a username, if one does.
        Args:
            username (str): The username to look up.
        Returns:
            return (AdminModel | None): The admin, or None when free.
        """
        stmt = select(AdminModel).where(col(AdminModel.username) == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_paged(
        self,
        q: str | None,
        is_super_admin: bool | None,
        offset: int,
        limit: int,
        id_match: int | None = None,
    ) -> PagedType[AdminModel]:
        """
        Desc: Get a filtered page of admins, newest first, with its count.
        Args:
            q (str | None): Free text over username.
            is_super_admin (bool | None): Whether to keep only super admins,
                or only plain ones.
            offset (int): Rows to skip.
            limit (int): Page size.
            id_match (int | None): Internal id a numeric query decoded to.
        Returns:
            return (PagedType[AdminModel]): The page and the total count.
        """
        clauses: list[ColumnElement[bool]] = []
        if q is not None:
            clause = col(AdminModel.username).ilike(f"%{q}%")
            if id_match is not None:
                clause = clause | (col(AdminModel.id) == id_match)
            clauses.append(clause)
        if is_super_admin is not None:
            clauses.append(
                col(AdminModel.is_super_admin).is_(is_super_admin)
            )
        stmt = (
            select(AdminModel)
            .where(*clauses)
            .order_by(col(AdminModel.id).desc())
        )
        paged = await self._paginate(stmt, offset, limit)
        return paged
