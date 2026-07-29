from datetime import datetime

from pydantic import Field, computed_field

from src.common.bases.schemas import BaseIDOutput, BaseOutput
from src.modules.price.sources.config.constants import (
    SOURCE_ID_ENCRYPTION,
    SourceIDField,
)
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.errors import SourceErrorInfo


class SourceConfigOut(BaseOutput):
    source_id: SourceIDField
    timeout: int
    # credentials are write-only: an admin sets them, nobody reads them back,
    # so they are carried for the flags below and dropped from the output
    headers_credentials: dict[str, str] | None = Field(
        default=None, exclude=True
    )
    auth_credentials: dict[str, str] | None = Field(default=None, exclude=True)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def has_headers_credentials(self) -> bool:
        """
        Desc: Tell whether the source carries request headers.
        Returns:
            return (bool): True when header credentials are set.
        """
        return self.headers_credentials is not None

    @computed_field
    @property
    def has_auth_credentials(self) -> bool:
        """
        Desc: Tell whether the source carries auth credentials.
        Returns:
            return (bool): True when auth credentials are set.
        """
        return self.auth_credentials is not None


class SourceOut(BaseIDOutput):
    __encryption__ = SOURCE_ID_ENCRYPTION

    title: str
    code: SourceCode
    website_url: str
    icon_url: str
    primary_color: str
    source_type: SourceSwitch
    error: SourceErrorInfo | None
    created_at: datetime
    updated_at: datetime


class SourceWithConfigOut(SourceOut):
    config: SourceConfigOut | None = None
