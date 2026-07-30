from dishka.integrations.taskiq import FromDishka, inject

from src.core.logger import logger
from src.modules.price.engine.interfaces import IRunnerService
from src.tasks.broker import broker


@broker.task(
    task_name="engine.crawl_all",
    queue_name="engine_queue",
    schedule=[{"interval": 30}],
)
@inject(patch_module=True)
async def crawl_all_sources(
    service: FromDishka[IRunnerService],
) -> bool:
    cached = await service.run()
    logger.info("crawl cached readings: %s", cached)
    return cached
