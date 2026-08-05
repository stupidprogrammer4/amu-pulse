from typing import Annotated

from pydantic import Field

from src.common.bases.dtos import BaseDTO
from src.common.types import (
    PageType,
    PasswordType,
    PerPageType,
    ValueType,
)

UsernameType = Annotated[str, Field(pattern=r"^[A-Za-z0-9_]{3,55}$")]


class AdminCreate(BaseDTO):
    username: UsernameType
    password: PasswordType
    is_super_admin: bool = False


class AdminUpdate(BaseDTO):
    is_super_admin: bool | None = None


class AdminSetUsername(BaseDTO):
    username: UsernameType


class AdminSetPassword(BaseDTO):
    password: PasswordType


class AdminSearch(BaseDTO):
    q: ValueType | None = None
    is_super_admin: bool | None = None
    page: PageType = 1
    per_page: PerPageType = 20
