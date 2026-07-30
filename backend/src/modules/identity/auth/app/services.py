from datetime import timedelta

from src.common.bases.services import BaseIDService
from src.common.errors.exceptions import (
    ConflictException,
    NotFoundException,
    UnAuthorizedException,
)
from src.common.utils import date_utils
from src.common.utils.crypto_utils import (
    hash_password,
    hash_sha256,
    verify_password,
)
from src.common.utils.jwt_utils import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.core.config import Settings
from src.modules.identity.auth.config import resources
from src.modules.identity.auth.domain.dtos import (
    TokenRefresh,
    UserLogin,
    UserRegister,
)
from src.modules.identity.auth.domain.models import (
    LoginLogModel,
    RefreshTokenModel,
    UserModel,
)
from src.modules.identity.auth.domain.results import AuthResult, TokenPair
from src.modules.identity.auth.infra.repository import (
    LoginLogRepository,
    RefreshTokenRepository,
    RoleRepository,
    UserRepository,
)


class AuthService(BaseIDService[UserModel]):
    # the role a self-registering user gets; seeded by src/seeders/roles.py
    default_role_code = "user"
    max_failed_attempts = 5
    lockout_minutes = 40

    def __init__(
        self,
        repo: UserRepository,
        roles: RoleRepository,
        refresh_tokens: RefreshTokenRepository,
        login_logs: LoginLogRepository,
        settings: Settings,
    ) -> None:
        """
        Desc: Build the service with its repositories and app settings.
        Args:
            repo (UserRepository): The user repository.
            roles (RoleRepository): The role repository.
            refresh_tokens (RefreshTokenRepository): Stored refresh
                tokens, used for rotation and revocation.
            login_logs (LoginLogRepository): The login-attempt log.
            settings (Settings): App settings (JWT and crypto config).
        """
        self.repo = repo
        self.roles = roles
        self.refresh_tokens = refresh_tokens
        self.login_logs = login_logs
        self.settings = settings

    def _issue_tokens(self, user: UserModel) -> TokenPair:
        """
        Desc: Sign a fresh access/refresh token pair for a user.
        Args:
            user (UserModel): The user the tokens are issued for.
        Returns:
            return (TokenPair): The signed access and refresh tokens.
        """
        subject = str(user.id)
        access = create_access_token(
            subject,
            self.settings.jwt.secret_key,
            expires_minutes=self.settings.jwt.access_token_expire_minutes,
            algorithm=self.settings.jwt.algorithm,
            extra_claims={
                "mobile": user.mobile,
                "role": user.role.code,
                "permissions": user.role.permissions,
            },
        )
        refresh = create_refresh_token(
            subject,
            self.settings.jwt.secret_key,
            expires_minutes=self.settings.jwt.refresh_token_expire_minutes,
            algorithm=self.settings.jwt.algorithm,
        )
        pair = TokenPair(access_token=access, refresh_token=refresh)
        return pair

    async def _issue_and_store_tokens(
        self,
        user: UserModel,
        ip: str | None,
        device: str | None,
    ) -> TokenPair:
        """
        Desc: Issue a token pair and persist the refresh token's hash.
        Args:
            user (UserModel): The user the tokens are issued for.
            ip (str | None): Caller ip, recorded on the refresh token.
            device (str | None): Caller user agent, recorded likewise.
        Returns:
            return (TokenPair): The issued access and refresh tokens.
        """
        tokens = self._issue_tokens(user)
        minutes = self.settings.jwt.refresh_token_expire_minutes
        await self.refresh_tokens.create(
            RefreshTokenModel(
                user_id=user.id,
                token_hash=hash_sha256(tokens.refresh_token),
                expires_at=date_utils.utc_now() + timedelta(minutes=minutes),
                device=device,
                ip=ip,
            )
        )
        return tokens

    async def _register_failed_attempt(self, user: UserModel) -> None:
        """
        Desc: Record a failed login and lock the account past the limit.
        Args:
            user (UserModel): The user whose password check failed.
        """
        attempts = user.failed_login_attempts + 1
        row: dict = {"failed_login_attempts": attempts}
        if attempts >= self.max_failed_attempts:
            minutes = self.lockout_minutes
            row["locked_until"] = date_utils.utc_now() + timedelta(
                minutes=minutes
            )
        await self.repo.update_by_id(user.id, row)

    async def register(
        self,
        data: UserRegister,
        ip: str | None,
        device: str | None,
    ) -> AuthResult:
        """
        Desc: Register a new user and issue tokens for them.
        Args:
            data (UserRegister): Mobile, password and optional name.
            ip (str | None): Caller ip, recorded on the refresh token.
            device (str | None): Caller user agent, recorded likewise.
        Returns:
            return (AuthResult): The created user and its tokens.
        """
        existing = await self.repo.get_by_mobile(data.mobile)
        if existing is not None:
            raise ConflictException(
                message=f"mobile {data.mobile} is already registered",
                message_code=resources.MOBILE_CONFLICT,
                unique_dict={"mobile": data.mobile},
            )
        role = await self.roles.get_by_code(self.default_role_code)
        if role is None:
            raise NotFoundException(
                message=f"default role '{self.default_role_code}' is "
                "not seeded",
                message_code=resources.ROLE_MISCONFIGURED,
                entity="Role",
                identifier="code",
                identifier_value=self.default_role_code,
            )
        password_hash = hash_password(
            data.password, pepper=self.settings.crypto.password_salt
        )
        user = await self.repo.create(
            UserModel(
                mobile=data.mobile,
                password_hash=password_hash,
                full_name=data.full_name,
                role_id=role.id,
            )
        )
        # the create() RETURNING clause doesn't carry the relationship —
        # attach it from what we already fetched instead of re-querying
        user.role = role
        tokens = await self._issue_and_store_tokens(user, ip, device)
        result = AuthResult(user=user, tokens=tokens)
        return result

    async def login(
        self,
        data: UserLogin,
        ip: str | None,
        device: str | None,
    ) -> AuthResult:
        """
        Desc: Verify credentials and issue tokens for a user.
        Args:
            data (UserLogin): Mobile and password to verify.
            ip (str | None): Caller ip, recorded on the log and token.
            device (str | None): Caller user agent, recorded likewise.
        Returns:
            return (AuthResult): The authenticated user and its tokens.
        """
        user = await self.repo.get_by_mobile(data.mobile)
        now = date_utils.utc_now()
        locked = (
            user is not None
            and user.locked_until is not None
            and user.locked_until > now
        )
        valid = (
            not locked
            and user is not None
            and user.is_active
            and verify_password(
                data.password,
                user.password_hash,
                pepper=self.settings.crypto.password_salt,
            )
        )
        await self.login_logs.create(
            LoginLogModel(
                user_id=user.id if user is not None else None,
                mobile=data.mobile,
                ip=ip,
                device=device,
                success=valid,
            )
        )
        if not valid:
            if user is not None and not locked:
                await self._register_failed_attempt(user)
            message_code = (
                resources.ACCOUNT_LOCKED
                if locked
                else resources.INVALID_CREDENTIALS
            )
            raise UnAuthorizedException(
                message="invalid mobile or password",
                message_code=message_code,
            )
        await self.repo.update_by_id(
            user.id,
            {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login_at": now,
                "last_login_ip": ip,
            },
        )
        tokens = await self._issue_and_store_tokens(user, ip, device)
        result = AuthResult(user=user, tokens=tokens)
        return result

    async def refresh(
        self,
        data: TokenRefresh,
        ip: str | None,
        device: str | None,
    ) -> AuthResult:
        """
        Desc: Rotate a refresh token: revoke it and issue a new pair.
        Args:
            data (TokenRefresh): The refresh token to redeem.
            ip (str | None): Caller ip, recorded on the new token.
            device (str | None): Caller user agent, recorded likewise.
        Returns:
            return (AuthResult): The owning user and its new tokens.
        """
        payload = decode_token(
            data.refresh_token,
            self.settings.jwt.secret_key,
            algorithm=self.settings.jwt.algorithm,
            expected_type=TokenType.REFRESH,
        )
        stored = await self.refresh_tokens.get_active_by_hash(
            hash_sha256(data.refresh_token)
        )
        if stored is None:
            raise UnAuthorizedException(
                message="refresh token is unknown or already used",
                message_code=resources.REFRESH_TOKEN_INVALID,
            )
        user_id = int(payload["sub"])
        user = await self.repo.get_by_id_with_role(user_id)
        user = self._check_for_id_existence(user_id, user)
        if not user.is_active:
            raise UnAuthorizedException(
                message="user is inactive",
                message_code=resources.INACTIVE_USER,
            )
        await self.refresh_tokens.revoke_by_id(stored.id)
        tokens = await self._issue_and_store_tokens(user, ip, device)
        result = AuthResult(user=user, tokens=tokens)
        return result

    async def logout(self, data: TokenRefresh) -> None:
        """
        Desc: Revoke a refresh token so it can no longer be redeemed.
        Args:
            data (TokenRefresh): The refresh token to revoke.
        """
        stored = await self.refresh_tokens.get_active_by_hash(
            hash_sha256(data.refresh_token)
        )
        if stored is not None:
            await self.refresh_tokens.revoke_by_id(stored.id)

    async def get_by_id(self, id: int) -> UserModel:
        """
        Desc: Get a user by id, with its role loaded.
        Args:
            id (int): ID of the user.
        Returns:
            return (UserModel): The found user.
        """
        user = await self.repo.get_by_id_with_role(id)
        user = self._check_for_id_existence(id, user)
        return user