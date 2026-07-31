from dishka import Provider, Scope, provide

from src.modules.identity.auth.app.services import AuthService
from src.modules.identity.auth.infra.repository import (
    LoginLogRepository,
    RefreshTokenRepository,
    RoleRepository,
    UserRepository,
)
from src.modules.identity.auth.interfaces import IAuthService


class AuthProvider(Provider):
    scope = Scope.REQUEST

    user_repo = provide(UserRepository)
    role_repo = provide(RoleRepository)
    refresh_token_repo = provide(RefreshTokenRepository)
    login_log_repo = provide(LoginLogRepository)
    auth_service = provide(AuthService, provides=IAuthService)