from dataclasses import dataclass

from src.modules.price.sources.domain.enums import SourceCode


@dataclass(frozen=True, slots=True)
class LoginContext:
    code: SourceCode
    id: int
    auth_credentials: dict[str, str]
