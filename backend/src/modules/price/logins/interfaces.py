from typing import Protocol, Sequence

from src.modules.price.logins.domain.quotes import LoginQuote
from src.modules.price.sources.domain.enums import SourceCode


class ISourceLoginService(Protocol):
    async def login(self, code: SourceCode) -> bool: ...

    async def login_by_id(self, source_id: int) -> bool: ...

    async def login_codes(self, codes: Sequence[SourceCode]) -> int: ...

    async def login_all(self) -> int: ...

    async def _try_to_login_all(
        self,
        codes: Sequence[SourceCode],
    ) -> Sequence[LoginQuote]: ...

    async def _save_all_credentials(
        self,
        quotes: Sequence[LoginQuote],
    ) -> int: ...
