from src.infra.postgres.repository.base import PGReader
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.engine.domain.context import AssetContext, SourceContext


class AssetReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)

    async def read(self) -> AssetContext:
        ...


class SourceReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)

    async def read(self) -> SourceContext:
        ...
