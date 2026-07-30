from dataclasses import dataclass

from src.modules.identity.auth.domain.models import UserModel


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: UserModel
    tokens: TokenPair


@dataclass(frozen=True, slots=True)
class CurrentUserData:
    # built straight from the access token's claims — no DB hit per request
    id: int
    mobile: str
    role: str
    permissions: list[str]