from typing import Mapping, Sequence

from pydantic import TypeAdapter, ValidationError

from src.infra.redis.client import RedisClient, resolve
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.engine.domain.results import (
    AssetPriceResult,
    BubbleResult,
    SourcePriceResult,
)


class AssetPriceCache:
    namespace = "assets:price"

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    def _decode(self, raw: str | None) -> AssetPriceResult | None:
        result = None
        if raw is not None:
            try:
                result = AssetPriceResult.model_validate_json(raw)
            except ValidationError:
                # an older result shape is a miss, not a crash
                result = None
        return result

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
        # redis refuses an empty mapping, and resolving nothing is normal
        if mapping:
            await resolve(
                self.redis.client.hset(self.namespace, mapping=mapping)
            )

    async def get(self, code: AssetCode) -> AssetPriceResult | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        result = self._decode(raw)
        return result

    async def get_many(
        self,
        codes: Sequence[AssetCode],
    ) -> dict[AssetCode, AssetPriceResult]:
        found: dict[AssetCode, AssetPriceResult] = {}
        if codes:
            fields = [code.value for code in codes]
            raws = await resolve(
                self.redis.client.hmget(self.namespace, fields)
            )
            for code, raw in zip(codes, raws):
                result = self._decode(raw)
                if result is not None:
                    found[code] = result
        return found

    async def get_all(self) -> dict[AssetCode, AssetPriceResult]:
        known = {code.value: code for code in AssetCode}
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found: dict[AssetCode, AssetPriceResult] = {}
        for field, raw in stored.items():
            # a field left behind by a retired AssetCode is not ours to read
            code = known.get(field)
            result = self._decode(raw)
            if code is not None and result is not None:
                found[code] = result
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

    def _decode(self, raw: str | None) -> list[SourcePriceResult] | None:
        results = None
        if raw is not None:
            try:
                results = self.adapter.validate_json(raw)
            except ValidationError:
                # an older result shape is a miss, not a crash
                results = None
        return results

    async def set(
        self,
        code: AssetCode,
        results: Sequence[SourcePriceResult],
    ) -> None:
        payload = self.adapter.dump_json(list(results)).decode()
        await resolve(
            self.redis.client.hset(self.namespace, code.value, payload)
        )

    async def set_many(
        self,
        results: Mapping[AssetCode, Sequence[SourcePriceResult]],
    ) -> None:
        mapping = {
            code.value: self.adapter.dump_json(list(rows)).decode()
            for code, rows in results.items()
        }
        # redis refuses an empty mapping, and resolving nothing is normal
        if mapping:
            await resolve(
                self.redis.client.hset(self.namespace, mapping=mapping)
            )

    async def get(self, code: AssetCode) -> list[SourcePriceResult] | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        results = self._decode(raw)
        return results

    async def get_many(
        self,
        codes: Sequence[AssetCode],
    ) -> dict[AssetCode, list[SourcePriceResult]]:
        found: dict[AssetCode, list[SourcePriceResult]] = {}
        if codes:
            fields = [code.value for code in codes]
            raws = await resolve(
                self.redis.client.hmget(self.namespace, fields)
            )
            for code, raw in zip(codes, raws):
                results = self._decode(raw)
                if results is not None:
                    found[code] = results
        return found

    async def get_all(self) -> dict[AssetCode, list[SourcePriceResult]]:
        known = {code.value: code for code in AssetCode}
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found: dict[AssetCode, list[SourcePriceResult]] = {}
        for field, raw in stored.items():
            # a field left behind by a retired AssetCode is not ours to read
            code = known.get(field)
            results = self._decode(raw)
            if code is not None and results is not None:
                found[code] = results
        return found

    async def remove(self, code: AssetCode) -> None:
        await resolve(self.redis.client.hdel(self.namespace, code.value))

    async def clear(self) -> None:
        await resolve(self.redis.client.delete(self.namespace))


class BubbleCache:
    namespace = "bubble:price"

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    def _decode(self, raw: str | None) -> BubbleResult | None:
        result = None
        if raw is not None:
            try:
                result = BubbleResult.model_validate_json(raw)
            except ValidationError:
                # an older result shape is a miss, not a crash
                result = None
        return result

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
        # redis refuses an empty mapping, and resolving nothing is normal
        if mapping:
            await resolve(
                self.redis.client.hset(self.namespace, mapping=mapping)
            )

    async def get(self, code: AssetCode) -> BubbleResult | None:
        raw = await resolve(self.redis.client.hget(self.namespace, code.value))
        result = self._decode(raw)
        return result

    async def get_many(
        self,
        codes: Sequence[AssetCode],
    ) -> dict[AssetCode, BubbleResult]:
        found: dict[AssetCode, BubbleResult] = {}
        if codes:
            fields = [code.value for code in codes]
            raws = await resolve(
                self.redis.client.hmget(self.namespace, fields)
            )
            for code, raw in zip(codes, raws):
                result = self._decode(raw)
                if result is not None:
                    found[code] = result
        return found

    async def get_all(self) -> dict[AssetCode, BubbleResult]:
        known = {code.value: code for code in AssetCode}
        stored = await resolve(self.redis.client.hgetall(self.namespace))
        found: dict[AssetCode, BubbleResult] = {}
        for field, raw in stored.items():
            # a field left behind by a retired AssetCode is not ours to read
            code = known.get(field)
            result = self._decode(raw)
            if code is not None and result is not None:
                found[code] = result
        return found

    async def remove(self, code: AssetCode) -> None:
        await resolve(self.redis.client.hdel(self.namespace, code.value))

    async def clear(self) -> None:
        await resolve(self.redis.client.delete(self.namespace))
