import logging
from typing import Any

from events import Ping

from src.consumers.registry import broker

logger = logging.getLogger(__name__)


@broker.task(task_name=Ping.name)
async def on_ping(payload: dict[str, Any]) -> None:
    event = Ping.model_validate(payload)
    logger.info("ping from api sent at %s: %s", event.sent_at, event.note)
