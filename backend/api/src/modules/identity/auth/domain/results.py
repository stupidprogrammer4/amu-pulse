from dataclasses import dataclass

from src.modules.identity.admins.domain.models import AdminModel


@dataclass(frozen=True, slots=True)
class AdminAuthType:
    access_token: str
    refresh_token: str
    admin: AdminModel
