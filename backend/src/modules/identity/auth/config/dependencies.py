from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.common.utils.jwt_utils import TokenType, decode_token
from src.core.config import get_settings
from src.modules.identity.auth.config.constants import USER_ID_ENCRYPTION
from src.modules.identity.auth.domain.results import CurrentUserData
from src.web.dependencies import decode_path_id

_bearer_scheme = HTTPBearer(auto_error=True)


def _resolve_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(_bearer_scheme)
    ],
) -> CurrentUserData:
    """
    Desc: Resolve the acting user straight from an access token's claims.
    Args:
        credentials (HTTPAuthorizationCredentials): The Authorization
            header, extracted by the bearer scheme.
    Returns:
        return (CurrentUserData): The token's subject, mobile, role and
            permissions — no DB lookup needed.
    """
    settings = get_settings()
    payload = decode_token(
        credentials.credentials,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
        expected_type=TokenType.ACCESS,
    )
    current_user = CurrentUserData(
        id=int(payload["sub"]),
        mobile=payload["mobile"],
        role=payload["role"],
        permissions=payload.get("permissions", []),
    )
    return current_user


# the acting user, resolved from the request's Authorization header —
# import this in ANY module's router to guard a route, e.g.:
#   from src.modules.identity.auth.config.dependencies import CurrentUser
#   async def my_route(user: CurrentUser, ...): ...
#   if "orders.manage" not in user.permissions: raise ForbiddenException(...)
CurrentUser = Annotated[CurrentUserData, Depends(_resolve_current_user)]

# the public user id in a route path, decoded to the internal one
UserID = Annotated[int, Depends(decode_path_id(USER_ID_ENCRYPTION, "User"))]