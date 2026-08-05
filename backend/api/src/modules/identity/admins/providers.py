from dishka import Provider, Scope, provide

from src.modules.identity.admins.app.services import AdminService
from src.modules.identity.admins.infra.repository import AdminRepository
from src.modules.identity.admins.interfaces import IAdminService


class AdminProvider(Provider):
    scope = Scope.REQUEST

    admin_repo = provide(AdminRepository)
    admin_service = provide(AdminService, provides=IAdminService)
