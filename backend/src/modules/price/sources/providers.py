from dishka import Provider, Scope, provide

from src.modules.price.sources.interfaces import ISourceService
from src.modules.price.sources.app.services import SourceService
from src.modules.price.sources.infra.repository import SourceRepository


class SourceProvider(Provider):
    scope = Scope.REQUEST

    source_repo = provide(SourceRepository)
    source_service = provide(SourceService, provides=ISourceService)
