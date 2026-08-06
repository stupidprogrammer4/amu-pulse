from abc import ABC, abstractmethod

import httpx

from src.modules.price.logins.domain.context import LoginContext
from src.modules.price.logins.domain.quotes import LoginError, LoginQuote
from src.modules.price.sources.domain.enums import ErrorType, SourceCode


class AbstractLogin(ABC):
    timeout = 30.0

    def __init__(self, source: LoginContext) -> None:
        super().__init__()
        self.source = source

    async def login(self) -> LoginQuote:
        try:
            credentials = await self._issue()
            quote = LoginQuote.granted(
                self.source.code, self.source.id, credentials
            )
        except httpx.HTTPError as exc:
            quote = self._refused(ErrorType.HTTP_ERROR, exc)
        except Exception as exc:
            quote = self._refused(ErrorType.LOGICAL_ERROR, exc)
        return quote

    def _refused(self, kind: ErrorType, exc: Exception) -> LoginQuote:
        quote = LoginQuote.refused(
            self.source.code,
            self.source.id,
            LoginError(
                error_type=kind,
                message=f"{type(exc).__name__}: {exc}",
            ),
        )
        return quote

    @abstractmethod
    async def _issue(self) -> dict[str, str]: ...


class MirrokniLogin(AbstractLogin):
    shopkeeper_id = "4c8d255e-80b3-ec11-9aaf-00505600229b"
    login_url = "https://pnl.mirrokni.ir/auth/LoginPass"
    end_sessions_url = "https://pnl.mirrokni.ir/Auth/EndSessions"
    profile_url = "https://pnlapi.mirrokni.ir/api/Profile/GetProfile"

    async def _issue(self) -> dict[str, str]:
        secret = self.source.auth_credentials
        payload = {
            "CaptchaToken": "",
            "UserName": secret.get("username", ""),
            "Password": secret.get("password", ""),
            "RememberMe": False,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.login_url, json=payload)
            data = resp.json()["Data"]
            if data.get("user") is None:
                resp = await client.post(self.end_sessions_url, json=payload)
                data = resp.json()["Data"]
            token = data["user"]["token"]
            headers = {
                "Authorization": f"Bearer {token}",
                "shopkeeperid": self.shopkeeper_id,
            }
            resp = await client.get(self.profile_url, headers=headers)
            headers["SessionId"] = resp.json()["Data"]["SessionId"]
        return headers


LOGINS: dict[SourceCode, type[AbstractLogin]] = {
    SourceCode.MIRROKNI: MirrokniLogin,
}
