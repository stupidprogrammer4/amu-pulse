from dishka.integrations.taskiq import FromDishka, inject

from src.core.logger import logger
from src.modules.chart.ticker.interfaces import (
    IPriceSnapshotService,
    ISourcePriceSnapshotService,
)
from src.tasks.broker import broker


@broker.task(
    task_name="ticker.snapshot_prices",
    queue_name="ticker_queue",
    schedule=[{"cron": "*/5 * * * *"}],
)
@inject(patch_module=True)
async def snapshot_prices(
    service: FromDishka[IPriceSnapshotService],
) -> bool:
    written = await service.snapshot_all()
    logger.info("asset prices snapshotted: %s", written)
    return written


@broker.task(
    task_name="ticker.snapshot_source_prices",
    queue_name="ticker_queue",
    schedule=[{"cron": "*/5 * * * *"}],
)
@inject(patch_module=True)
async def snapshot_source_prices(
    service: FromDishka[ISourcePriceSnapshotService],
) -> bool:
    written = await service.snapshot_all()
    logger.info("source prices snapshotted: %s", written)
    return written
