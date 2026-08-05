from dishka import Provider, Scope, provide

from src.modules.identity.auth.app.services import AdminAuthService
from src.modules.identity.auth.interfaces import IAdminAuthService


class AuthProvider(Provider):
    scope = Scope.REQUEST

    admin_auth_service = provide(AdminAuthService, provides=IAdminAuthService)
