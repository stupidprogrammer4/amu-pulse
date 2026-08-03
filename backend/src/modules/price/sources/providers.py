from dishka import Provider, Scope, provide

from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceErrorService,
    SourceMetaService,
    SourceService,
)
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.modules.price.sources.interfaces import (
    ISourceConfigService,
    ISourceErrorService,
    ISourceMetaService,
    ISourceService,
)


class SourceProvider(Provider):
    scope = Scope.REQUEST

    source_repo = provide(SourceRepository)
    source_config_repo = provide(SourceConfigRepository)
    source_config_service = provide(
        SourceConfigService, provides=ISourceConfigService
    )
    source_service = provide(SourceService, provides=ISourceService)
    source_error_service = provide(
        SourceErrorService, provides=ISourceErrorService
    )
    source_meta_service = provide(
        SourceMetaService, provides=ISourceMetaService
    )
