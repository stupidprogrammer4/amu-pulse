from events import App, build_consumer

from src.settings import get_settings

settings = get_settings()

broker = build_consumer(settings.rabbitmq.url, App.AI)
