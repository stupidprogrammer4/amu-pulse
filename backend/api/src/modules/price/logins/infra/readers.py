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
        super().__init__(uow)

    async def read_by_codes(
        self,
        codes: Sequence[SourceCode],
    ) -> Sequence[LoginContext]:
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
