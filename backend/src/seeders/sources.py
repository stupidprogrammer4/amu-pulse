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
    # --- supplier: Iranian gold shops ---
    SourceSeed(
        SourceCode.TALALAND,
        "طلالند",
        "https://talaland.net",
        "#c9a227",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.MIRROKNI,
        "میرکنی",
        "https://mirrokni.ir",
        "#8b6f2f",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.DIGIKALA,
        "دیجی‌کالا",
        "https://www.digikala.com",
        "#ef4056",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.TALINE,
        "تلاین",
        "https://tlyn.ir",
        "#d4af37",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.GOLDIKA,
        "گلدیکا",
        "https://goldika.ir",
        "#e8b923",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.MELIGOLD,
        "ملی‌گلد",
        "https://melligold.com",
        "#b8860b",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.MILIGOLD,
        "میلی‌گلد",
        "https://milli.gold",
        "#f2c94c",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.TECHNOGOLD,
        "تکنوگلد",
        "https://technogold.gold",
        "#a67c00",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.WALLGOLD,
        "وال‌گلد",
        "https://wallgold.ir",
        "#caa64a",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.TALASEA,
        "طلاسی",
        "https://talasea.ir",
        "#dfb244",
        _SUPPLIER,
    ),
    SourceSeed(
        SourceCode.NOGHRESEA,
        "نقره‌سی",
        "https://noghresea.ir",
        "#9aa5ab",
        _SUPPLIER,
    ),
    # --- iran_market: rial-denominated gold and USD quotes ---
    SourceSeed(
        SourceCode.TGJU,
        "شبکه اطلاع‌رسانی طلا و ارز",
        "https://www.tgju.org",
        "#1f6feb",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.ALANCHAND,
        "الان چند",
        "https://alanchand.com",
        "#00a884",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.NAVASAN,
        "نوسان",
        "https://www.navasan.net",
        "#e2574c",
        _IRAN,
    ),
    SourceSeed(
        SourceCode.NERKH_API,
        "نرخ‌ای‌پی‌آی",
        "https://nerkh-api.ir",
        "#5b6ee1",
        _IRAN,
    ),
    # --- global_market: XAU spot ---
    SourceSeed(
        SourceCode.GOLDAPI_IO,
        "GoldAPI.io",
        "https://www.goldapi.io",
        "#ffd700",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.GOLDAPI_NET,
        "GoldAPI.net",
        "https://goldapi.net",
        "#e6c200",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.GOLD_API,
        "Gold-API",
        "https://gold-api.com",
        "#f4c542",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.GOLDPRICE_DEV,
        "GoldPrice.dev",
        "https://goldprice.dev",
        "#d9a441",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.METALPRICE_API,
        "MetalpriceAPI",
        "https://metalpriceapi.com",
        "#2f80ed",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.METALS_API,
        "Metals-API",
        "https://metals-api.com",
        "#356ac3",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.UNIRATE_API,
        "UniRateAPI",
        "https://unirateapi.com",
        "#6b4eff",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.COMMODITY_PRICE_API,
        "CommodityPriceAPI",
        "https://commoditypriceapi.com",
        "#0f9d58",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.XAUS,
        "XAUS",
        "https://xaus.com",
        "#c0932e",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.TWELVE_DATA,
        "Twelve Data",
        "https://twelvedata.com",
        "#00b4d8",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.EODHD,
        "EODHD",
        "https://eodhd.com",
        "#1b3a5c",
        _GLOBAL,
    ),
    # --- global_market: USD and the rest of the FX board ---
    SourceSeed(
        SourceCode.OPEN_EXCHANGE_RATES,
        "Open Exchange Rates",
        "https://openexchangerates.org",
        "#00857d",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.FIXER,
        "Fixer",
        "https://fixer.io",
        "#3d5afe",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.CURRENCY_LAYER,
        "Currencylayer",
        "https://currencylayer.com",
        "#12a5b3",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.EXCHANGERATE_API,
        "ExchangeRate-API",
        "https://www.exchangerate-api.com",
        "#2b6cb0",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.EXCHANGERATES_API,
        "ExchangeRatesAPI",
        "https://exchangeratesapi.io",
        "#4a5568",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.FREE_CURRENCY_API,
        "FreeCurrencyAPI",
        "https://freecurrencyapi.com",
        "#38a169",
        _GLOBAL,
    ),
    SourceSeed(
        SourceCode.FRANKFURTER,
        "Frankfurter",
        "https://frankfurter.dev",
        "#805ad5",
        _GLOBAL,
    ),
]


def _favicon(website_url: str) -> str:
    """
    Desc: Build a source's icon url via google's favicon service.
    Args:
        website_url (str): Home page url of the source.
    Returns:
        return (str): Url of the source's 64px favicon.
    """
    domain = (
        website_url.removeprefix("https://").removeprefix("http://").strip("/")
    )
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"


def _service(uow: PGUnitOfWork) -> SourceService:
    """
    Desc: Build the source service over the unit of work.
    Args:
        uow (PGUnitOfWork): Unit of work the service writes through.
    Returns:
        return (SourceService): The assembled service.
    """
    configs = SourceConfigService(SourceConfigRepository(uow))
    service = SourceService(SourceRepository(uow), configs)
    return service


async def seed_sources(uow: PGUnitOfWork) -> list[SourceModel]:
    """
    Desc: Create every missing source through the service, with its config.
    Args:
        uow (PGUnitOfWork): Unit of work the service writes through.
    Returns:
        return (list[SourceModel]): The sources created by this run.
    """
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
