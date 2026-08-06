from dishka import Provider, Scope, provide

from src.modules.identity.auth.app.services import AdminAuthService
from src.modules.identity.auth.infra.denylist import TokenDenylist
from src.modules.identity.auth.interfaces import IAdminAuthService


class AuthProvider(Provider):
    scope = Scope.REQUEST

    denylist = provide(TokenDenylist)
    admin_auth_service = provide(
        AdminAuthService, provides=IAdminAuthService
    )
