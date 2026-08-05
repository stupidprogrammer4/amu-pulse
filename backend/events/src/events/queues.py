from __future__ import annotations

from enum import StrEnum

from taskiq_aio_pika.exchange import Exchange
from taskiq_aio_pika.queue import Queue


class App(StrEnum):
    """The backend apps that can send or receive an event."""

    API = "api"
    AI = "ai"


exchange = Exchange(name="amu.events")


def queue_name(app: App) -> str:
    """
    Desc: Name the queue an app receives its events on.
    Args:
        app (App): The receiving app.
    Returns:
        return (str): The queue name, which is also its routing key.
    """
    name = f"{app.value}.events"
    return name


def queue(app: App) -> Queue:
    """
    Desc: Declare one app's inbox on the shared exchange.
    Args:
        app (App): The receiving app.
    Returns:
        return (Queue): The queue bound to that app's routing key.
    """
    declared = Queue(name=queue_name(app))
    return declared


def all_queues() -> list[Queue]:
    """
    Desc: Declare every app's inbox, which a publisher needs so that the
        routing label picks one instead of defaulting to the only queue.
    Returns:
        return (list[Queue]): One queue per app.
    """
    queues = [queue(app) for app in App]
    return queues
