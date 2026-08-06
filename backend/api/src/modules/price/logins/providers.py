from dishka import Provider, Scope, provide

from src.modules.price.logins.app.services import SourceLoginService
from src.modules.price.logins.infra.readers import LoginReader
from src.modules.price.logins.interfaces import ISourceLoginService
from src.modules.price.logins.tasks.login import SourceUnauthorizedHandler


class LoginProvider(Provider):
    scope = Scope.REQUEST

    login_reader = provide(LoginReader)
    source_login_service = provide(
        SourceLoginService, provides=ISourceLoginService
    )
    source_unauthorized_handler = provide(SourceUnauthorizedHandler)
