from typing import Mapping, Sequence

from pydantic import TypeAdapter

from src.infra.redis.client import RedisClient, resolve
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.results import (
    AssetPriceResult,
    BubbleResult,
    SourceBubbleResult,
    SourcePriceResult,
)
from src.modules.price.symbols.domain.enums import SymbolCode


class AssetPriceCache:
    namespace = "assets:price"

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    async def set(
        self,
        code: AssetCode,
        result: AssetPriceResult,
    ) -> None:
        await resolve(
            self.redis.client.hset(
                self.namespace, code.value, result.model_dump_json()
            )
        )

    async def set_many(
        self,
        results: Mapping[AssetCode, AssetPriceResult],
    ) -> None:
        mapping = {
            code.value: result.model_dump_json()
            for code, result in results.items()
        }
        await resolve(self.redis.client.hset(self.namespace, mapping=mapping))

    async def get(self, code: AssetCode) -> AssetPriceResult | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        result = None
        if raw is not None:
            result = AssetPriceResult.model_validate_json(raw)
        return result

    async def get_many(
        self,
        codes: Sequence[AssetCode],
    ) -> dict[AssetCode, AssetPriceResult]:
        fields = [code.value for code in codes]
        raws = await resolve(self.redis.client.hmget(self.namespace, fields))
        found = {
            code: AssetPriceResult.model_validate_json(raw)
            for code, raw in zip(codes, raws)
            if raw is not None
        }
        return found

    async def get_all(self) -> dict[AssetCode, AssetPriceResult]:
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found = {
            AssetCode(field): AssetPriceResult.model_validate_json(raw)
            for field, raw in stored.items()
        }
        return found

    async def remove(self, code: AssetCode) -> None:
        await resolve(self.redis.client.hdel(self.namespace, code.value))

    async def clear(self) -> None:
        await resolve(self.redis.client.delete(self.namespace))


class SourcePriceCache:
    namespace = "sources:price"
    # a list of results per field, so one adapter parses the whole field
    adapter = TypeAdapter(list[SourcePriceResult])

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    async def set(
        self,
        code: SymbolCode,
        results: Sequence[SourcePriceResult],
    ) -> None:
        payload = self.adapter.dump_json(list(results)).decode()
        await resolve(
            self.redis.client.hset(self.namespace, code.value, payload)
        )

    async def set_many(
        self,
        results: Mapping[SymbolCode, Sequence[SourcePriceResult]],
    ) -> None:
        mapping = {
            code.value: self.adapter.dump_json(list(rows)).decode()
            for code, rows in results.items()
        }
        await resolve(self.redis.client.hset(self.namespace, mapping=mapping))

    async def get(self, code: SymbolCode) -> list[SourcePriceResult] | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        results = None
        if raw is not None:
            results = self.adapter.validate_json(raw)
        return results

    async def get_many(
        self,
        codes: Sequence[SymbolCode],
    ) -> dict[SymbolCode, list[SourcePriceResult]]:
        fields = [code.value for code in codes]
        raws = await resolve(self.redis.client.hmget(self.namespace, fields))
        found = {
            code: self.adapter.validate_json(raw)
            for code, raw in zip(codes, raws)
            if raw is not None
        }
        return found

    async def get_all(self) -> dict[SymbolCode, list[SourcePriceResult]]:
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found = {
            SymbolCode(field): self.adapter.validate_json(raw)
            for field, raw in stored.items()
        }
        return found

    async def remove(self, code: SymbolCode) -> None:
        await resolve(self.redis.client.hdel(self.namespace, code.value))

    async def clear(self) -> None:
        await resolve(self.redis.client.delete(self.namespace))


class BubbleCache:
    namespace = "bubble:price"

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    async def set(self, code: AssetCode, result: BubbleResult) -> None:
        await resolve(
            self.redis.client.hset(
                self.namespace, code.value, result.model_dump_json()
            )
        )

    async def set_many(
        self,
        results: Mapping[AssetCode, BubbleResult],
    ) -> None:
        mapping = {
            code.value: result.model_dump_json()
            for code, result in results.items()
        }
        await resolve(self.redis.client.hset(self.namespace, mapping=mapping))

    async def get(self, code: AssetCode) -> BubbleResult | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        result = None
        if raw is not None:
            result = BubbleResult.model_validate_json(raw)
        return result

    async def get_many(
        self,
        codes: Sequence[AssetCode],
    ) -> dict[AssetCode, BubbleResult]:
        fields = [code.value for code in codes]
        raws = await resolve(self.redis.client.hmget(self.namespace, fields))
        found = {
            code: BubbleResult.model_validate_json(raw)
            for code, raw in zip(codes, raws)
            if raw is not None
        }
        return found

    async def get_all(self) -> dict[AssetCode, BubbleResult]:
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found = {
            AssetCode(field): BubbleResult.model_validate_json(raw)
            for field, raw in stored.items()
        }
        return found

    async def remove(self, code: AssetCode) -> None:
        await resolve(self.redis.client.hdel(self.namespace, code.value))

    async def clear(self) -> None:
        await resolve(self.redis.client.delete(self.namespace))


class BubbleSourceCache:
    namespace = "sources:bubble"
    adapter = TypeAdapter(list[SourceBubbleResult])

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    async def set(
        self,
        code: AssetCode,
        results: Sequence[SourceBubbleResult],
    ) -> None:
        payload = self.adapter.dump_json(list(results)).decode()
        await resolve(
            self.redis.client.hset(self.namespace, code.value, payload)
        )

    async def set_many(
        self,
        results: Mapping[AssetCode, Sequence[SourceBubbleResult]],
    ) -> None:
        mapping = {
            code.value: self.adapter.dump_json(list(rows)).decode()
            for code, rows in results.items()
        }
        await resolve(self.redis.client.hset(self.namespace, mapping=mapping))

    async def get(self, code: AssetCode) -> list[SourceBubbleResult] | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        results = None
        if raw is not None:
            results = self.adapter.validate_json(raw)
        return results

    async def get_many(
        self,
        codes: Sequence[AssetCode],
    ) -> dict[AssetCode, list[SourceBubbleResult]]:
        fields = [code.value for code in codes]
        raws = await resolve(self.redis.client.hmget(self.namespace, fields))
        found = {
            code: self.adapter.validate_json(raw)
            for code, raw in zip(codes, raws)
            if raw is not None
        }
        return found

    async def get_all(self) -> dict[AssetCode, list[SourceBubbleResult]]:
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found = {
            AssetCode(field): self.adapter.validate_json(raw)
            for field, raw in stored.items()
        }
        return found

    async def remove(self, code: AssetCode) -> None:
        await resolve(self.redis.client.hdel(self.namespace, code.value))

    async def clear(self) -> None:
        await resolve(self.redis.client.delete(self.namespace))
