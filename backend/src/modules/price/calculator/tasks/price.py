from dishka.integrations.taskiq import FromDishka, inject

from src.core.logger import logger
from src.modules.price.calculator.interfaces import ICalculatorService
from src.tasks.broker import broker


@broker.task(
    task_name="calculator.calculate_asset",
    queue_name="calculator_queue",
)
@inject(patch_module=True)
async def calculate_asset(
    asset_id: int,
    service: FromDishka[ICalculatorService],
) -> int:
    price = await service.calculate(asset_id)
    logger.info("asset %s priced at %s", asset_id, price)
    return price
