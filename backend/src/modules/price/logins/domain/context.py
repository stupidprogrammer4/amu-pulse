from dataclasses import dataclass

from src.modules.price.sources.domain.enums import SourceCode


@dataclass(frozen=True, slots=True)
class LoginContext:
    # only what a login needs: which source, and the secret to exchange
    code: SourceCode
    id: int
    # never None: the reader drops a source that holds no secret
    auth_credentials: dict[str, str]
