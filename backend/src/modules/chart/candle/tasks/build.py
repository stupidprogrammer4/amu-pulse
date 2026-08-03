from dishka.integrations.taskiq import FromDishka, inject

from src.core.logger import logger
from src.modules.chart.candle.domain.enums import TimeFrame
from src.modules.chart.candle.interfaces import (
    ICandleService,
    ISourceCandleService,
)
from src.tasks.broker import broker


@broker.task(
    task_name="candle.build_from_cache",
    queue_name="candle_queue",
    # on the five-minute marks, the moment a window closes
    schedule=[{"cron": "*/5 * * * *"}],
)
@inject(patch_module=True)
async def build_from_cache(
    candles: FromDishka[ICandleService],
    sources: FromDishka[ISourceCandleService],
) -> int:
    priced = await candles.build_from_cache()
    quoted = await sources.build_from_cache()
    logger.info("closed window written down: %s + %s", priced, quoted)
    return priced + quoted


@broker.task(
    task_name="candle.roll_timeframe",
    queue_name="candle_queue",
    schedule=[
        {
            "cron": "1 * * * *",
            "cron_offset": "Asia/Tehran",
            "kwargs": {"tf": TimeFrame.HOURLY.value},
        },
        {
            "cron": "2 */5 * * *",
            "cron_offset": "Asia/Tehran",
            "kwargs": {"tf": TimeFrame.FIVE_HOURLY.value},
        },
        {
            "cron": "3 0 * * *",
            "cron_offset": "Asia/Tehran",
            "kwargs": {"tf": TimeFrame.DAILY.value},
        },
    ],
)
@inject(patch_module=True)
async def roll_timeframe(
    tf: TimeFrame,
    candles: FromDishka[ICandleService],
    sources: FromDishka[ISourceCandleService],
) -> int:
    # a schedule hands the timeframe over as its own value
    frame = TimeFrame(tf)
    priced = await candles.build_timeframe_from_rolled(frame)
    quoted = await sources.build_timeframe_from_rolled(frame)
    logger.info("%s rolled up: %s + %s", frame.value, priced, quoted)
    return priced + quoted
