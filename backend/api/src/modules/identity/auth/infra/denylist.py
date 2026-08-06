from datetime import UTC, datetime

from src.infra.redis.client import RedisClient

NAMESPACE = "auth:revoked"


class TokenDenylist:
    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    async def revoke(self, jti: str, expires_at: int) -> None:
        """
        Desc: Mark one token as spent. The entry lives exactly as long as
            the token would have, so the list never outgrows what is still
            forgeable.
        Args:
            jti (str): The token's own id.
            expires_at (int): The token's exp claim, in whole seconds.
        """
        now = int(datetime.now(UTC).timestamp())
        ttl = expires_at - now
        if ttl <= 0:
            return
        await self.redis.client.set(f"{NAMESPACE}:{jti}", "1", ex=ttl)

    async def is_revoked(self, jti: str) -> bool:
        """
        Desc: Read whether a token has already been spent.
        Args:
            jti (str): The token's own id.
        Returns:
            return (bool): Whether it was revoked.
        """
        found = await self.redis.client.exists(f"{NAMESPACE}:{jti}")
        return bool(found)
