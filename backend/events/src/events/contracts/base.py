from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel


class Event(BaseModel):
    """
    Base for every payload that crosses an app boundary.

    `name` is the wire name: the publisher routes on it and the consumer
    registers its handler under it, so changing one breaks the other.
    """

    name: ClassVar[str]
