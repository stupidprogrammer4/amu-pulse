from typing import Any, Protocol, runtime_checkable

from pydantic import AnyUrl, BaseModel


class BaseDTO(BaseModel):
    def to_row(self, *, exclude_unset: bool = True) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, AnyUrl) else value
            for key, value in self.model_dump(
                exclude_unset=exclude_unset
            ).items()
        }


@runtime_checkable
class SupportsToRow(Protocol):
    def to_row(self, *, exclude_unset: bool = ...) -> dict[str, Any]: ...
