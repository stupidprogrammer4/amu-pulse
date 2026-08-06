from dataclasses import dataclass

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.infra.repository import AssetRepository
from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.domain.dtos import SymbolCreate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.domain.models import SymbolModel
from src.modules.price.symbols.infra.repository import SymbolRepository


@dataclass(frozen=True, slots=True)
class SymbolSeed:
    code: SymbolCode
    title: str
    description: str
    asset: AssetCode
    currency: CurrencyType
    primary_color: str


SYMBOLS: list[SymbolSeed] = [
    SymbolSeed(
        SymbolCode.GOLD18_GRAM,
        "گرم طلای ۱۸ عیار",
        "قیمت هر گرم طلای ۱۸ عیار به ریال",
        AssetCode.GOLD18,
        CurrencyType.RIAL,
        "#1baf7a",
    ),
    SymbolSeed(
        SymbolCode.GOLD18_MAZANE,
        "مظنه آب‌شده",
        "قیمت مثقال آب‌شده هفده عیار به ریال",
        AssetCode.GOLD18,
        CurrencyType.RIAL,
        "#eda100",
    ),
    SymbolSeed(
        SymbolCode.XAU_OUNCE,
        "انس جهانی طلا",
        "قیمت هر اونس طلا در بازار جهانی به دلار",
        AssetCode.GOLD18,
        CurrencyType.USD,
        "#e87ba4",
    ),
    SymbolSeed(
        SymbolCode.USD_RIAL,
        "دلار آمریکا",
        "نرخ برابری دلار آمریکا در برابر ریال",
        AssetCode.USD,
        CurrencyType.RIAL,
        "#4a3aa7",
    ),
]


async def seed_symbols(uow: PGUnitOfWork) -> list[SymbolModel]:
    service = SymbolService(SymbolRepository(uow))
    assets = await AssetRepository(uow).get_all()
    asset_ids = {asset.code: asset.id for asset in assets}

    existing = await service.get_all()
    taken = {symbol.code for symbol in existing}

    created: list[SymbolModel] = []
    for spec in SYMBOLS:
        asset_id = asset_ids.get(spec.asset)
        if spec.code in taken or asset_id is None:
            continue
        symbol = await service.create(
            SymbolCreate(
                title=spec.title,
                code=spec.code,
                asset_id=ASSET_ID_ENCRYPTION.encode(asset_id),
                currency=spec.currency,
                primary_color=spec.primary_color,
                description=spec.description,
            )
        )
        created.append(symbol)
    return created
