from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from src.common.errors.exceptions import (
    ForbiddenException,
    UnAuthorizedException,
)
from src.common.utils import jwt_utils
from src.core import resources
from src.core.config import get_settings
from src.modules.identity.auth.config.constants import ADMIN_TOKEN_ROLE


@dataclass(frozen=True, slots=True)
class AdminPrincipal:
    id: int
    username: str
    is_super_admin: bool


def _bearer(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnAuthorizedException(
            message="missing bearer token",
            message_code=resources.MISSING_TOKEN,
        )
    return token


def current_admin(request: Request) -> AdminPrincipal:
    """
    Desc: Read the signed-in admin off the Authorization header. Everything
        the guard needs is in the token, so a request costs no query — the
        price is that a change of role only lands on the next refresh.
    Args:
        request (Request): The incoming request.
    Returns:
        return (AdminPrincipal): Who the access token says is calling.
    """
    settings = get_settings()
    claims = jwt_utils.decode_token(
        _bearer(request),
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
        expected_type=jwt_utils.TokenType.ACCESS,
    )
    if claims.get("role") != ADMIN_TOKEN_ROLE:
        raise UnAuthorizedException(
            message="not an admin token",
            message_code=resources.INVALID_TOKEN,
        )
    return AdminPrincipal(
        id=int(claims["sub"]),
        username=str(claims.get("username", "")),
        is_super_admin=bool(claims.get("is_super_admin")),
    )


def super_admin(
    admin: Annotated[AdminPrincipal, Depends(current_admin)],
) -> AdminPrincipal:
    """
    Desc: Narrow the guard to super admins.
    Args:
        admin (AdminPrincipal): Who the access token says is calling.
    Returns:
        return (AdminPrincipal): The same principal, once it is super.
    """
    if not admin.is_super_admin:
        raise ForbiddenException(
            message="this route is for super admins",
            message_code=resources.INSUFFICIENT_SCOPE,
            user_id=admin.id,
        )
    return admin


# any signed-in admin
CurrentAdmin = Annotated[AdminPrincipal, Depends(current_admin)]

# only a super admin
SuperAdmin = Annotated[AdminPrincipal, Depends(super_admin)]

# the same two as router-level dependencies, for a router whose every route
# is guarded: one line on the APIRouter beats a parameter on every handler
admin_required = Depends(current_admin)
super_admin_required = Depends(super_admin)
