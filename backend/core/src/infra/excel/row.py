from typing import Any

from pydantic import BaseModel, Field


def Row(*, title: str | None = None, **kwargs: Any) -> Any:
    return Field(title=title, **kwargs)


class ExcelRow(BaseModel):
    @classmethod
    def titles(cls) -> list[str]:
        return [
            field.title or name for name, field in cls.model_fields.items()
        ]

    def cells(self) -> list[Any]:
        return [getattr(self, name) for name in type(self).model_fields]
