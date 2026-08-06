from events import EventBus, build_publisher

from src.core.config import get_settings

settings = get_settings()

event_broker = build_publisher(settings.rabbitmq.url)

event_bus = EventBus(event_broker)
