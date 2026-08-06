from src.core.config import Settings
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.identity.admins.app.services import AdminService
from src.modules.identity.admins.domain.dtos import AdminCreate
from src.modules.identity.admins.domain.models import AdminModel
from src.modules.identity.admins.infra.repository import AdminRepository


async def create_super_admin(
    uow: PGUnitOfWork,
    settings: Settings,
    username: str,
    password: str,
) -> tuple[AdminModel, bool]:
    repo = AdminRepository(uow)
    service = AdminService(repo, settings)

    existing = await repo.get_by_username(username)
    if existing is not None:
        return existing, False

    admin = await service.create(
        AdminCreate(
            username=username,
            password=password,
            is_super_admin=True,
        )
    )
    return admin, True
