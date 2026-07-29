from dataclasses import dataclass

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.bubbles.app.services import (
    BubbleConfigService,
    BubbleService,
)
from src.modules.price.bubbles.domain.dtos import BubbleCreate
from src.modules.price.bubbles.domain.models import BubbleModel
from src.modules.price.bubbles.infra.repository import (
    BubbleConfigRepository,
    BubbleRepository,
)


@dataclass(frozen=True, slots=True)
class BubbleSeed:
    code: AssetCode
    title: str
    description: str


BUBBLES: list[BubbleSeed] = [
    BubbleSeed(
        AssetCode.GOLD18,
        "حباب طلای ۱۸ عیار",
        "اختلاف قیمت بازار با ارزش ذاتی هر گرم طلای ۱۸ عیار",
    ),
]


def _service(uow: PGUnitOfWork) -> BubbleService:
    configs = BubbleConfigService(BubbleConfigRepository(uow))
    service = BubbleService(BubbleRepository(uow), configs)
    return service


async def seed_bubbles(uow: PGUnitOfWork) -> list[BubbleModel]:
    service = _service(uow)
    existing = await service.get_all()
    taken = {bubble.code for bubble in existing}

    created: list[BubbleModel] = []
    for spec in BUBBLES:
        if spec.code in taken:
            continue
        bubble = await service.create(
            BubbleCreate(
                title=spec.title,
                code=spec.code,
                description=spec.description,
            )
        )
        created.append(bubble)
    return created
