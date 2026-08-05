from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from src.settings import get_settings

settings = get_settings()

# ai's own queue, for work it schedules itself; cross-app traffic goes over
# the RabbitMQ event bus in events/ instead
broker = RedisStreamBroker(
    url=settings.taskiq.redis_url,
    max_connection_pool_size=settings.taskiq.max_connection_pool_size,
).with_result_backend(
    RedisAsyncResultBackend(
        settings.taskiq.redis_url,
        prefix_str="ai_taskiq_result",
        result_ex_time=60,
    )
)
