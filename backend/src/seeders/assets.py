from dataclasses import dataclass

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
)
from src.modules.price.assets.domain.dtos import AssetCreate
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
)


@dataclass(frozen=True, slots=True)
class AssetSeed:
    code: AssetCode
    title: str
    description: str


ASSETS: list[AssetSeed] = [
    AssetSeed(
        AssetCode.GOLD18,
        "طلای ۱۸ عیار",
        "مظنه آب‌شده و قیمت هر گرم طلای ۱۸ عیار",
    ),
    AssetSeed(
        AssetCode.USD,
        "دلار آمریکا",
        "نرخ برابری دلار آمریکا در برابر ریال",
    ),
]


def _service(uow: PGUnitOfWork) -> AssetService:
    configs = AssetConfigService(AssetConfigRepository(uow))
    service = AssetService(AssetRepository(uow), configs)
    return service


async def seed_assets(uow: PGUnitOfWork) -> list[AssetModel]:
    service = _service(uow)
    existing = await service.get_all()
    taken = {asset.code for asset in existing}

    created: list[AssetModel] = []
    for spec in ASSETS:
        if spec.code in taken:
            continue
        asset = await service.create(
            AssetCreate(
                title=spec.title,
                code=spec.code,
                description=spec.description,
            )
        )
        created.append(asset)
    return created
