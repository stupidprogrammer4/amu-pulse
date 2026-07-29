from src.infra.postgres.repository.base import PGIDRepository
from src.modules.price.sources.domain.models import SourceModel


class SourceRepository(PGIDRepository[SourceModel]):
    ...
