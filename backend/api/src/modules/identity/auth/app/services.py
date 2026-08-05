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

# what a login checks the offered password against when the username does not
# exist, so a caller cannot tell the two apart by how long the answer took
_DUMMY_HASH = crypto_utils.hash_password("no-such-admin")


class AdminAuthService:
    def __init__(self, admins: IAdminService, settings: Settings) -> None:
        """
        Desc: Build the service with the admin service and the JWT config.
        Args:
            admins (IAdminService): Reads admins and checks their passwords.
            settings (Settings): Read for the jwt section.
        """
        self.admins = admins
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
        # re-read the admin rather than trust the claims: a role or a
        # deletion that happened since the token was signed has to win
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
            # one message for both halves, so a wrong username and a wrong
            # password are indistinguishable to whoever is guessing
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
        # the refresh token carries the role only; everything a guard reads
        # off it comes from the access token it is traded for
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
