from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import aiofiles.os


class InvalidStoragePath(ValueError): ...


class LocalStorage:
    backend = "local"

    def __init__(self, base_path: str) -> None:
        self.base = Path(base_path or "media").resolve()

    def _resolve(self, path: str) -> Path:
        target = (self.base / path).resolve()
        if target != self.base and not target.is_relative_to(self.base):
            raise InvalidStoragePath(path)
        return target

    async def save_stream(
        self, path: str, chunks: AsyncIterator[bytes]
    ) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(target, "wb") as handle:
            async for chunk in chunks:
                await handle.write(chunk)
        return path

    async def move(self, src: str, dst: str) -> str:
        source = self._resolve(src)
        target = self._resolve(dst)
        target.parent.mkdir(parents=True, exist_ok=True)
        await aiofiles.os.replace(source, target)
        return dst

    def exists(self, path: str) -> bool:
        return self._resolve(path).is_file()

    async def stream(
        self, path: str, chunk_size: int = 64 * 1024
    ) -> AsyncIterator[bytes]:
        target = self._resolve(path)
        async with aiofiles.open(target, "rb") as handle:
            while chunk := await handle.read(chunk_size):
                yield chunk

    async def delete(self, path: str) -> None:
        target = self._resolve(path)
        if target.is_file():
            await aiofiles.os.remove(target)
