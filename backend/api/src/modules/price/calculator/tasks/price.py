from dishka.integrations.taskiq import FromDishka, inject

from src.core.logger import logger
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.infra.readers import AssetReader
from src.modules.price.calculator.interfaces import ICalculatorService
from src.tasks.broker import broker


@broker.task(
    task_name="calculator.calculate_usd",
    queue_name="calculator_queue",
    schedule=[{"interval": 20}],
)
@inject(patch_module=True)
async def calculate_usd(
    service: FromDishka[ICalculatorService],
) -> int:
    price = await service.calculate_usd()
    logger.info("dollar priced at %s", price)
    return price


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


@broker.task(
    task_name="calculator.reprice_asset",
    queue_name="calculator_queue",
)
@inject(patch_module=True)
async def reprice_asset(
    code: AssetCode,
    assets: FromDishka[AssetReader],
    service: FromDishka[ICalculatorService],
) -> int:
    asset_id = await assets.get_id_by_code(code)
    price = 0
    if asset_id is None:
        logger.warning("no asset carries the code %s", code)
    else:
        price = await service.calculate(asset_id)
        logger.info("asset %s repriced at %s", code, price)
    return price
