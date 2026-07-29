from __future__ import annotations

from math import gcd

__all__ = ["IDEncryption"]


class IDEncryption:
    __slots__ = ("_mod", "_coff", "_coff_inv", "_offset")

    def __init__(self, mod: int, coff: int, offset: int = 0) -> None:
        if mod < 2:
            raise ValueError(f"mod must be >= 2, got {mod}")
        if offset < 0:
            raise ValueError(f"offset must be >= 0, got {offset}")

        coff %= mod
        if coff == 0:
            raise ValueError("coff must not be a multiple of mod")

        g = gcd(coff, mod)
        if g != 1:
            raise ValueError(
                f"coff and mod must be coprime, but gcd(coff, mod) = {g}"
            )

        self._mod = mod
        self._coff = coff
        self._coff_inv = pow(coff, -1, mod)
        self._offset = offset

    @property
    def capacity(self) -> int:
        return self._mod

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def bounds(self) -> tuple[int, int]:
        return self._offset, self._offset + self._mod - 1

    def encode(self, id: int) -> int:
        if id < 0:
            raise ValueError(f"id must be >= 0, got {id}")
        if id >= self._mod:
            raise OverflowError(f"id {id} exceeds capacity {self._mod}")
        return self._offset + (id * self._coff) % self._mod

    def decode(self, public_id: int) -> int:
        shifted = public_id - self._offset
        if not 0 <= shifted < self._mod:
            low, high = self.bounds
            raise ValueError(
                f"public_id {public_id} out of range [{low}, {high}]"
            )
        return (shifted * self._coff_inv) % self._mod

    def try_decode(self, public_id: int) -> int | None:
        try:
            return self.decode(public_id)
        except ValueError:
            return None

    @staticmethod
    def is_valid_coff(mod: int, coff: int) -> bool:
        return mod >= 2 and gcd(coff % mod, mod) == 1

    def __repr__(self) -> str:
        text = (
            f"{type(self).__name__}(mod={self._mod}, "
            f"coff=<hidden>, offset={self._offset})"
        )
        return text
