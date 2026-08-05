from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from events.contracts.base import Event


class Ping(Event):
    """Proves the bus is wired end to end. Carries nothing of its own."""

    name: ClassVar[str] = "pulse.ping"

    sent_at: datetime
    note: str = ""
