from events import EventBus, build_publisher

from src.core.config import get_settings

settings = get_settings()

# outbound only: this broker is never run by `taskiq worker`, so it declares
# the queues and publishes to them without consuming any
event_broker = build_publisher(settings.rabbitmq.url)

event_bus = EventBus(event_broker)
