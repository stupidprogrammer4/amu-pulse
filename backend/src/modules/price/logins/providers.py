from dishka import Provider, Scope, provide

from src.modules.price.logins.app.services import SourceLoginService
from src.modules.price.logins.infra.readers import LoginReader
from src.modules.price.logins.interfaces import ISourceLoginService
from src.modules.price.logins.tasks.login import SourceUnauthorizedHandler


class LoginProvider(Provider):
    scope = Scope.REQUEST

    # owns no table: reads through its own reader, writes via sources
    login_reader = provide(LoginReader)
    source_login_service = provide(
        SourceLoginService, provides=ISourceLoginService
    )
    # the event bus resolves the handler itself, so it has to be bound here
    source_unauthorized_handler = provide(SourceUnauthorizedHandler)
