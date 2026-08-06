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
    if not admin.is_super_admin:
        raise ForbiddenException(
            message="this route is for super admins",
            message_code=resources.INSUFFICIENT_SCOPE,
            user_id=admin.id,
        )
    return admin


CurrentAdmin = Annotated[AdminPrincipal, Depends(current_admin)]

SuperAdmin = Annotated[AdminPrincipal, Depends(super_admin)]

admin_required = Depends(current_admin)
super_admin_required = Depends(super_admin)
