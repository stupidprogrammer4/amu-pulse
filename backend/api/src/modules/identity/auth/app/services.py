from src.common.errors.exceptions import (
    NotFoundException,
    UnAuthorizedException,
)
from src.common.utils import crypto_utils, jwt_utils
from src.core import resources
from src.core.config import Settings
from src.modules.identity.admins.domain.models import AdminModel
from src.modules.identity.admins.interfaces import IAdminService
from src.modules.identity.auth.config.constants import ADMIN_TOKEN_ROLE
from src.modules.identity.auth.domain.results import AdminAuthType
from src.modules.identity.auth.infra.denylist import TokenDenylist

_DUMMY_HASH = crypto_utils.hash_password("no-such-admin")


class AdminAuthService:
    def __init__(
        self,
        admins: IAdminService,
        denylist: TokenDenylist,
        settings: Settings,
    ) -> None:
        self.admins = admins
        self.denylist = denylist
        self.jwt = settings.jwt

    async def login(self, username: str, password: str) -> AdminAuthType:
        """
        Desc: Sign an admin in with their username and password.
        Args:
            username (str): The username offered.
            password (str): The plain password offered.
        Returns:
            return (AdminAuthType): The token pair and the admin.
        """
        admin = await self._authenticate(username, password)
        return self._issue(admin)

    async def refresh(self, refresh_token: str) -> AdminAuthType:
        """
        Desc: Trade a refresh token for a fresh pair.
        Args:
            refresh_token (str): The refresh token to rotate.
        Returns:
            return (AdminAuthType): The new token pair and the admin.
        """
        claims = jwt_utils.decode_token(
            refresh_token,
            self.jwt.secret_key,
            algorithm=self.jwt.algorithm,
            expected_type=jwt_utils.TokenType.REFRESH,
        )
        jti = str(claims.get("jti", ""))
        if await self.denylist.is_revoked(jti):
            raise UnAuthorizedException(
                message="this refresh token has already been used",
                message_code=resources.INVALID_TOKEN,
            )
        await self.denylist.revoke(jti, int(claims["exp"]))
        admin = await self.admins.get_by_id(int(claims["sub"]))
        return self._issue(admin)

    async def _authenticate(
        self, username: str, password: str
    ) -> AdminModel:
        try:
            admin = await self.admins.get_by_username(username)
        except NotFoundException:
            admin = None

        if admin is None:
            await self.admins.verify_password(
                AdminModel(username="", hashed_password=_DUMMY_HASH), password
            )
            ok = False
        else:
            ok = await self.admins.verify_password(admin, password)

        if not ok or admin is None:
            raise UnAuthorizedException(
                message="wrong username or password",
                message_code=resources.INVALID_CREDENTIALS,
            )
        return admin

    def _issue(self, admin: AdminModel) -> AdminAuthType:
        subject = str(admin.id)
        claims = {
            "role": ADMIN_TOKEN_ROLE,
            "username": admin.username,
            "is_super_admin": admin.is_super_admin,
        }
        access = jwt_utils.create_access_token(
            subject,
            self.jwt.secret_key,
            expires_minutes=self.jwt.access_token_expire_minutes,
            algorithm=self.jwt.algorithm,
            extra_claims=claims,
        )
        refresh = jwt_utils.create_refresh_token(
            subject,
            self.jwt.secret_key,
            expires_minutes=self.jwt.refresh_token_expire_minutes,
            algorithm=self.jwt.algorithm,
            extra_claims={"role": ADMIN_TOKEN_ROLE},
        )
        return AdminAuthType(
            access_token=access, refresh_token=refresh, admin=admin
        )
