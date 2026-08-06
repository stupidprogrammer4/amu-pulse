from typing import Self

from src.common.bases.schemas import BaseOutput
from src.modules.identity.admins.domain.schemas import AdminOut
from src.modules.identity.auth.domain.results import AdminAuthType


class AdminAuthOut(BaseOutput):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    admin: AdminOut

    @classmethod
    def from_auth(cls, auth: AdminAuthType) -> Self:
        return cls(
            access_token=auth.access_token,
            refresh_token=auth.refresh_token,
            admin=AdminOut.from_obj(auth.admin),
        )
