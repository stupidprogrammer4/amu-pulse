from typing import Annotated

from pydantic import Field

from src.common.bases.dtos import BaseDTO
from src.common.types import (
    ColorType,
    LStrType,
    MediaUrlType,
    PageType,
    PerPageType,
    StrType,
    ValueType,
)
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch

TimeoutType = Annotated[int, Field(ge=1, le=60)]


class SourceCreate(BaseDTO):
    title: StrType
    code: SourceCode
    website_url: LStrType
    icon_url: MediaUrlType
    primary_color: ColorType
    source_type: SourceSwitch


class SourceUpdate(BaseDTO):
    title: StrType | None = None
    website_url: LStrType | None = None
    icon_url: MediaUrlType | None = None
    primary_color: ColorType | None = None
    source_type: SourceSwitch | None = None


class SourceSearch(BaseDTO):
    q: ValueType | None = None
    source_types: list[SourceSwitch] | None = None
    has_error: bool | None = None
    page: PageType = 1
    per_page: PerPageType = 20


class SourceConfigUpdate(BaseDTO):
    timeout: TimeoutType | None = None
    headers_credentials: dict[str, str] | None = None
    auth_credentials: dict[str, str] | None = None
