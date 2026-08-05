from __future__ import annotations

from taskiq_aio_pika import AioPikaBroker

from events.queues import App, all_queues, exchange, queue


def build_publisher(url: str) -> AioPikaBroker:
    """
    Desc: Build the broker an app publishes with. It knows every queue so
        that the routing label chooses the destination; it is never run as a
        worker, so it consumes none of them.
    Args:
        url (str): The RabbitMQ connection URL.
    Returns:
        return (AioPikaBroker): A broker for outbound events only.
    """
    broker = AioPikaBroker(
        url=url,
        exchange=exchange,
        task_queues=all_queues(),
    )
    return broker


def build_consumer(url: str, app: App) -> AioPikaBroker:
    """
    Desc: Build the broker an app consumes with. It knows only its own queue,
        so a worker on it never eats another app's events.
    Args:
        url (str): The RabbitMQ connection URL.
        app (App): The app whose inbox to consume.
    Returns:
        return (AioPikaBroker): A broker for inbound events only.
    """
    broker = AioPikaBroker(
        url=url,
        exchange=exchange,
        task_queues=[queue(app)],
    )
    return broker
