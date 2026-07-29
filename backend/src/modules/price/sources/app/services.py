from src.common.bases.services import BaseIDService
from src.modules.price.sources.domain.dtos import SourceCreate, SourceUpdate
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.sources.infra.repository import SourceRepository


class SourceService(BaseIDService[SourceModel]):
    def __init__(self, repo: SourceRepository) -> None:
        self.repo = repo

    async def create(self, data: SourceCreate) -> SourceModel:
        raise NotImplementedError

    async def update(self, id: int, data: SourceUpdate) -> SourceModel:
        raise NotImplementedError

    async def get_by_id(self, id: int) -> SourceModel:
        raise NotImplementedError

    async def remove(self, id: int) -> SourceModel:
        raise NotImplementedError
