from dataclasses import dataclass

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.sources.app.services import (
    SourceConfigService,
    SourceService,
)
from src.modules.price.sources.domain.dtos import SourceCreate
from src.modules.price.sources.domain.enums import SourceCode, SourceSwitch
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)


@dataclass(frozen=True, slots=True)
class SourceSeed:
    code: SourceCode
    title: str
    website_url: str
    primary_color: str
    switch: SourceSwitch


_SUPPLIER = SourceSwitch.SUPPLIER
_IRAN = SourceSwitch.IRAN_MARKET
_GLOBAL = SourceSwitch.GLOBAL_MARKET


SOURCES: list[SourceSeed] = [
    SourceSeed(
        SourceCode.TALALAND,
        "طلالند",
        "https://talaland.net",
        "#9e2b5a",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.MIRROKNI,
        "میرکنی",
        "https://mirrokni.ir",
        "#db9416",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.DIGIKALA,
        "دیجی‌کالا",
        "https://www.digikala.com",
        "#0a712d",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.TALINE,
        "تلاین",
        "https://tlyn.ir",
        "#1ab6df",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.GOLDIKA,
        "گلدیکا",
        "https://goldika.ir",
        "#6844a9",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.MELIGOLD,
        "ملی‌گلد",
        "https://melligold.com",
        "#f4778d",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.MILIGOLD,
        "میلی‌گلد",
        "https://milli.gold",
        "#84630a",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.TECHNOGOLD,
        "تکنوگلد",
        "https://technogold.gold",
        "#2ac180",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.WALLGOLD,
        "وال‌گلد",
        "https://wallgold.ir",
        "#0c729b",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.TALASEA,
        "طلاسی",
        "https://talasea.ir",
        "#be88f0",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.NOGHRESEA,
        "نقره‌سی",
        "https://noghresea.ir",
        "#a32b35",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.TGJU,
        "شبکه اطلاع‌رسانی طلا و ارز",
        "https://www.tgju.org",
        "#c0a316",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.ALANCHAND,
        "الان چند",
        "https://alanchand.com",
        "#0f886a",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.NAVASAN,
        "نوسان",
        "https://www.navasan.net",
        "#39adfc",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.NERKH_API,
        "نرخ‌ای‌پی‌آی",
        "https://nerkh-api.ir",
        "#803a95",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.WALLEX,
        "والکس",
        "https://wallex.ir",
        "#f67b65",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.GOLDAPI_IO,
        "GoldAPI.io",
        "https://www.goldapi.io",
        "#726c0a",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.GOLDAPI_NET,
        "GoldAPI.net",
        "https://goldapi.net",
        "#1abea8",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.GOLD_API,
        "Gold-API",
        "https://gold-api.com",
        "#085dae",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.GOLDPRICE_DEV,
        "GoldPrice.dev",
        "https://goldprice.dev",
        "#d87ed5",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.METALPRICE_API,
        "MetalpriceAPI",
        "https://metalpriceapi.com",
        "#9b3b07",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.METALS_API,
        "Metals-API",
        "https://metals-api.com",
        "#a0b023",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.UNIRATE_API,
        "UniRateAPI",
        "https://unirateapi.com",
        "#15a09b",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.COMMODITY_PRICE_API,
        "CommodityPriceAPI",
        "https://commoditypriceapi.com",
        "#79a2fc",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.XAUS,
        "XAUS",
        "https://xaus.com",
        "#92317a",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.TWELVE_DATA,
        "Twelve Data",
        "https://twelvedata.com",
        "#ee8539",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.EODHD,
        "EODHD",
        "https://eodhd.com",
        "#4b6908",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.OPEN_EXCHANGE_RATES,
        "Open Exchange Rates",
        "https://openexchangerates.org",
        "#1abac3",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.FIXER,
        "Fixer",
        "https://fixer.io",
        "#4850b3",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.CURRENCY_LAYER,
        "Currencylayer",
        "https://currencylayer.com",
        "#ea78b3",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.EXCHANGERATE_API,
        "ExchangeRate-API",
        "https://www.exchangerate-api.com",
        "#864e07",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.EXCHANGERATES_API,
        "ExchangeRatesAPI",
        "https://exchangeratesapi.io",
        "#72bb55",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.FREE_CURRENCY_API,
        "FreeCurrencyAPI",
        "https://freecurrencyapi.com",
        "#149db2",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.FRANKFURTER,
        "Frankfurter",
        "https://frankfurter.dev",
        "#9d95fc",
        _GLOBAL,
    ),
]


def _favicon(website_url: str) -> str:
    domain = (
        website_url.removeprefix("https://").removeprefix("http://").strip("/")
    )
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"


def _service(uow: PGUnitOfWork) -> SourceService:
    configs = SourceConfigService(SourceConfigRepository(uow))
    service = SourceService(SourceRepository(uow), configs)
    return service


async def seed_sources(uow: PGUnitOfWork) -> list[SourceModel]:
    service = _service(uow)
    existing = await service.get_all()
    taken = {source.code for source in existing}

    created: list[SourceModel] = []
    for spec in SOURCES:
        if spec.code in taken:
            continue
        source = await service.create(
            SourceCreate(
                title=spec.title,
                code=spec.code,
                website_url=spec.website_url,
                icon_url=_favicon(spec.website_url),
                primary_color=spec.primary_color,
                source_type=spec.switch,
            )
        )
        created.append(source)
    return created
