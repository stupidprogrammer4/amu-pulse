from typing import Optional, Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGReader
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.logins.domain.context import LoginContext
from src.modules.price.sources.domain.enums import SourceCode
from src.modules.price.sources.domain.models import (
    SourceConfigModel,
    SourceModel,
)


class LoginReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def read_by_codes(
        self,
        codes: Sequence[SourceCode],
    ) -> Sequence[LoginContext]:
        """
        Desc: Read the named sources' login secrets, oldest first.
        Args:
            codes (Sequence[SourceCode]): Codes of the sources to log into.
        Returns:
            return (Sequence[LoginContext]): One context per source that
                actually holds a secret.
        """
        stmt = (
            select(
                SourceModel.id,
                SourceModel.code,
                SourceConfigModel.auth_credentials,
            )
            .join(
                SourceConfigModel,
                col(SourceConfigModel.source_id) == col(SourceModel.id),
            )
            .where(
                col(SourceModel.code).in_(codes),
                col(SourceConfigModel.auth_credentials).isnot(None),
            )
            .order_by(col(SourceModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            LoginContext(code=code, id=id, auth_credentials=secret)
            for id, code, secret in rows
        ]

    async def read(self, source_id: int) -> Optional[LoginContext]:
        """
        Desc: Read one source's login secret by its id.
        Args:
            source_id (int): ID of the source to log into.
        Returns:
            return (Optional[LoginContext]): The context, or None when
                the source has no row, no config or no secret.
        """
        stmt = (
            select(
                SourceModel.id,
                SourceModel.code,
                SourceConfigModel.auth_credentials,
            )
            .join(
                SourceConfigModel,
                col(SourceConfigModel.source_id) == col(SourceModel.id),
            )
            .where(
                col(SourceModel.id) == source_id,
                col(SourceConfigModel.auth_credentials).isnot(None),
            )
        )
        result = await self.session.execute(stmt)
        row = result.first()
        context = None
        if row is not None:
            id, code, secret = row
            context = LoginContext(code=code, id=id, auth_credentials=secret)
        return context
