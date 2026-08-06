from dishka import Provider, Scope, provide

from src.modules.ops.logs.app.services import LogService
from src.modules.ops.logs.infra.repository import LogRepository
from src.modules.ops.logs.interfaces import ILogService


class LogProvider(Provider):
    scope = Scope.REQUEST

    log_repo = provide(LogRepository)
    log_service = provide(LogService, provides=ILogService)
