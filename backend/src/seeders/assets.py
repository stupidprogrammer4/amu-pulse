from dataclasses import dataclass

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
    AssetSwitchService,
)
from src.modules.price.assets.domain.dtos import (
    AssetCreate,
    AssetSwitchBatchCreate,
    AssetSwitchCreate,
)
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.sources.domain.enums import SourceSwitch


@dataclass(frozen=True, slots=True)
class AssetSeed:
    code: AssetCode
    title: str
    description: str
    # the markets that price it, best level first
    switches: list[AssetSwitchCreate]


ASSETS: list[AssetSeed] = [
    AssetSeed(
        AssetCode.GOLD18,
        "طلای ۱۸ عیار",
        "مظنه آب‌شده و قیمت هر گرم طلای ۱۸ عیار",
        [
            AssetSwitchCreate(switch=SourceSwitch.GLOBAL_MARKET, priority=0),
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=0),
            AssetSwitchCreate(switch=SourceSwitch.IRAN_MARKET, priority=1),
        ],
    ),
    AssetSeed(
        AssetCode.USD,
        "دلار آمریکا",
        "نرخ برابری دلار آمریکا در برابر ریال",
        [
            AssetSwitchCreate(switch=SourceSwitch.IRAN_MARKET, priority=0),
        ],
    ),
]


def _service(uow: PGUnitOfWork) -> AssetService:
    configs = AssetConfigService(AssetConfigRepository(uow))
    service = AssetService(AssetRepository(uow), configs)
    return service


async def seed_assets(uow: PGUnitOfWork) -> list[AssetModel]:
    service = _service(uow)
    switches = AssetSwitchService(AssetSwitchRepository(uow))
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
        await switches.batch_create(
            asset.id,
            AssetSwitchBatchCreate(items=spec.switches),
        )
        created.append(asset)
    return created
