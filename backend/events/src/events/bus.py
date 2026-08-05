from __future__ import annotations

from typing import Any

from taskiq import AsyncBroker
from taskiq.kicker import AsyncKicker

from events.contracts.base import Event
from events.queues import App, queue_name


class EventBus:
    """Publishes events to another app's inbox over the shared exchange."""

    # the label taskiq-aio-pika reads the routing key from
    routing_label = "queue_name"

    def __init__(self, broker: AsyncBroker) -> None:
        self._broker = broker

    async def publish(
        self,
        event: Event,
        to: App,
    ) -> None:
        """
        Desc: Send one event to an app's inbox. Fire and forget — the sender
            never waits for the consumer.
        Args:
            event (Event): The payload to deliver.
            to (App): The app that should receive it.
        """
        kicker: AsyncKicker[Any, None] = AsyncKicker(
            task_name=type(event).name,
            broker=self._broker,
            labels={self.routing_label: queue_name(to)},
        )
        payload = event.model_dump(mode="json")
        await kicker.kiq(payload=payload)
