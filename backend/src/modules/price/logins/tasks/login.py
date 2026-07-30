from typing import Sequence

from dishka.integrations.taskiq import FromDishka, inject

from src.core.logger import logger
from src.modules.price.logins.config.constants import SOURCE_UNAUTHORIZED
from src.modules.price.logins.infra.gateways import LOGINS
from src.modules.price.logins.interfaces import ISourceLoginService
from src.modules.price.sources.domain.enums import SourceCode
from src.tasks.broker import broker
from src.tasks.events import on


@broker.task(
    task_name="logins.refresh_all",
    queue_name="logins_queue",
    # a session outlives a week, so a weekly sweep is enough
    schedule=[{"cron": "0 3 * * 5"}],
)
@inject(patch_module=True)
async def refresh_all_logins(
    service: FromDishka[ISourceLoginService],
) -> int:
    saved = await service.login_all()
    logger.info("refreshed %s of %s source logins", saved, len(LOGINS))
    return saved


@broker.task(
    task_name="logins.refresh_codes",
    queue_name="logins_queue",
)
@inject(patch_module=True)
async def refresh_logins(
    codes: Sequence[SourceCode],
    service: FromDishka[ISourceLoginService],
) -> int:
    saved = await service.login_codes(codes)
    logger.info("refreshed %s of %s requested logins", saved, len(codes))
    return saved


@on(SOURCE_UNAUTHORIZED)
class SourceUnauthorizedHandler:
    def __init__(self, service: ISourceLoginService) -> None:
        self.service = service

    async def handle(self, id: int) -> bool:
        # the bus speaks in ids; only sources that have a login can act on it
        saved = await self.service.login_by_id(id)
        return saved
