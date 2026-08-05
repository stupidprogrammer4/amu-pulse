from events import App, build_consumer

from src.settings import get_settings

settings = get_settings()

# inbound only: one queue, so a worker here never eats the api's events
broker = build_consumer(settings.rabbitmq.url, App.AI)
