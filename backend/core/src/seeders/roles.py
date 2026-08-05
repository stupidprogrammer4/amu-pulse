from dataclasses import dataclass

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.identity.auth.domain.models import RoleModel
from src.modules.identity.auth.infra.repository import RoleRepository


@dataclass(frozen=True, slots=True)
class RoleSeed:
    code: str
    title: str
    permissions: list[str]


ROLES: list[RoleSeed] = [
    RoleSeed("admin", "مدیر", ["*"]),
    RoleSeed("user", "کاربر", []),
]


async def seed_roles(uow: PGUnitOfWork) -> list[RoleModel]:
    repo = RoleRepository(uow)
    existing = await repo.get_all()
    taken = {role.code for role in existing}

    created: list[RoleModel] = []
    for spec in ROLES:
        if spec.code in taken:
            continue
        role = await repo.create(
            RoleModel(
                code=spec.code,
                title=spec.title,
                permissions=spec.permissions,
            )
        )
        created.append(role)
    return created
