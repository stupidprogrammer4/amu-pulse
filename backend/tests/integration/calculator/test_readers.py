import pytest

from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.app.services import (
    AssetConfigService,
    AssetService,
    AssetSwitchService,
)
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.dtos import (
    AssetConfigUpdate,
    AssetCreate,
    AssetSwitchCreate,
)
from src.modules.price.assets.domain.enums import AggregationType, AssetCode
from src.modules.price.assets.domain.models import AssetModel
from src.modules.price.assets.infra.repository import (
    AssetConfigRepository,
    AssetRepository,
    AssetSwitchRepository,
)
from src.modules.price.bubbles.app.services import (
    BubbleConfigService,
    BubbleService,
)
from src.modules.price.bubbles.domain.dtos import (
    BubbleConfigUpdate,
    BubbleCreate,
)
from src.modules.price.bubbles.infra.repository import (
    BubbleConfigRepository,
    BubbleRepository,
)
from src.modules.price.calculator.infra.readers import (
    AssetReader,
    BubbleReader,
    SwitchOrderReader,
    SymbolReader,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.symbols.app.services import SymbolService
from src.modules.price.symbols.domain.dtos import SymbolCreate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.infra.repository import SymbolRepository


def _assets(uow: PGUnitOfWork) -> tuple[AssetService, AssetConfigService]:
    """
    Desc: Build the asset services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (tuple[AssetService, AssetConfigService]): The two services.
    """
    configs = AssetConfigService(AssetConfigRepository(uow))
    return AssetService(AssetRepository(uow), configs), configs


def _bubbles(uow: PGUnitOfWork) -> tuple[BubbleService, BubbleConfigService]:
    """
    Desc: Build the bubble services over real repositories.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
    Returns:
        return (tuple[BubbleService, BubbleConfigService]): The two services.
    """
    configs = BubbleConfigService(BubbleConfigRepository(uow))
    return BubbleService(BubbleRepository(uow), configs), configs


async def _asset(
    uow: PGUnitOfWork,
    code: AssetCode = AssetCode.GOLD18,
) -> AssetModel:
    """
    Desc: Create one asset with its default config.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        code (AssetCode): Code of the asset to create.
    Returns:
        return (AssetModel): The created asset.
    """
    assets, _ = _assets(uow)
    asset = await assets.create(AssetCreate(title="طلا", code=code))
    return asset


async def _symbol(
    uow: PGUnitOfWork,
    asset: AssetModel,
    code: SymbolCode = SymbolCode.GOLD18_GRAM,
    currency: CurrencyType = CurrencyType.RIAL,
) -> None:
    """
    Desc: Create one symbol hanging off the given asset.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the symbol is quoted for.
        code (SymbolCode): Code of the symbol.
        currency (CurrencyType): What the line is priced in.
    """
    symbols = SymbolService(SymbolRepository(uow))
    await symbols.create(
        SymbolCreate(
            title="هر گرم طلای ۱۸ عیار",
            code=code,
            asset_id=ASSET_ID_ENCRYPTION.encode(asset.id),
            currency=currency,
        )
    )


async def _switch(
    uow: PGUnitOfWork,
    asset: AssetModel,
    switch: SourceSwitch,
    priority: int,
) -> None:
    """
    Desc: Put one market at the given level of an asset's pricing order.
    Args:
        uow (PGUnitOfWork): Unit of work to write through.
        asset (AssetModel): The asset the market prices.
        switch (SourceSwitch): The market to add.
        priority (int): Where it sits in the order; lower comes first.
    """
    switches = AssetSwitchService(AssetSwitchRepository(uow))
    await switches.create(
        asset.id,
        AssetSwitchCreate(switch=switch, priority=priority),
    )


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSymbolReader:
    async def test_it_reads_a_symbol_with_its_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await _symbol(uow, asset)

        found = await SymbolReader(uow).get_all()

        assert len(found) == 1
        assert found[0].symbol == SymbolCode.GOLD18_GRAM
        assert found[0].code == AssetCode.GOLD18
        assert found[0].asset_id == asset.id

    async def test_it_reads_every_line_of_every_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        await _symbol(uow, gold, SymbolCode.GOLD18_MAZANE)
        await _symbol(uow, dollar, SymbolCode.USD_RIAL)

        found = await SymbolReader(uow).get_all()

        assert [c.symbol for c in found] == [
            SymbolCode.GOLD18_GRAM,
            SymbolCode.GOLD18_MAZANE,
            SymbolCode.USD_RIAL,
        ]
        assert {c.code for c in found} == {AssetCode.GOLD18, AssetCode.USD}

    async def test_get_symbols_of_asset_narrows_to_one_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await _symbol(uow, gold, SymbolCode.GOLD18_GRAM)
        await _symbol(uow, dollar, SymbolCode.USD_RIAL)

        found = await SymbolReader(uow).get_symbols_of_asset(gold.id)

        assert [c.symbol for c in found] == [SymbolCode.GOLD18_GRAM]
        assert found[0].asset_id == gold.id

    async def test_an_asset_without_lines_reads_empty(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)

        found = await SymbolReader(uow).get_symbols_of_asset(asset.id)

        assert list(found) == []

    async def test_get_all_on_an_empty_table(self, uow: PGUnitOfWork) -> None:
        found = await SymbolReader(uow).get_all()

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestAssetReader:
    async def test_it_reads_an_asset_with_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)

        context = await AssetReader(uow).get_asset_config(asset.id)

        assert context is not None
        assert context.asset_id == asset.id
        assert context.code == AssetCode.GOLD18
        assert context.config.asset_id == asset.id
        assert context.config.agg_type == AggregationType.MEDIAN

    async def test_a_missing_asset_reads_as_none(
        self, uow: PGUnitOfWork
    ) -> None:
        context = await AssetReader(uow).get_asset_config(9999)

        assert context is None

    async def test_get_all_config_reads_every_asset(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)

        found = await AssetReader(uow).get_all_config()

        assert [c.asset_id for c in found] == [gold.id, dollar.id]

    async def test_a_paused_asset_is_still_read(
        self, uow: PGUnitOfWork
    ) -> None:
        # folding what is already cached costs nothing, so the scheduler
        # flag gates the crawl, not the calculation
        asset = await _asset(uow)

        found = await AssetReader(uow).get_all_config()

        assert [c.asset_id for c in found] == [asset.id]
        assert found[0].config.scheduler_on is False

    async def test_the_context_carries_the_aggregation_rule(
        self, uow: PGUnitOfWork
    ) -> None:
        # the calculator folds a line's readings by exactly this rule
        asset = await _asset(uow)
        _, configs = _assets(uow)
        await configs.update(
            asset.id,
            AssetConfigUpdate(agg_type=AggregationType.THIRD_QUARTILE),
        )

        context = await AssetReader(uow).get_asset_config(asset.id)

        assert context is not None
        assert context.config.agg_type == AggregationType.THIRD_QUARTILE

    async def test_get_all_config_on_an_empty_table(
        self, uow: PGUnitOfWork
    ) -> None:
        found = await AssetReader(uow).get_all_config()

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestBubbleReader:
    async def test_it_reads_a_bubble_with_its_config(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, _ = _bubbles(uow)
        created = await bubbles.create(
            BubbleCreate(title="حباب طلا", code=AssetCode.GOLD18)
        )

        context = await BubbleReader(uow).get_bubble_config(created.id)

        assert context is not None
        assert context.bubble_id == created.id
        assert context.code == AssetCode.GOLD18
        assert context.config.bubble_id == created.id
        assert context.config.agg_type == AggregationType.MEDIAN

    async def test_a_missing_bubble_reads_as_none(
        self, uow: PGUnitOfWork
    ) -> None:
        context = await BubbleReader(uow).get_bubble_config(9999)

        assert context is None

    async def test_get_all_reads_every_bubble(self, uow: PGUnitOfWork) -> None:
        bubbles, _ = _bubbles(uow)
        gold = await bubbles.create(
            BubbleCreate(title="حباب طلا", code=AssetCode.GOLD18)
        )
        dollar = await bubbles.create(
            BubbleCreate(title="حباب دلار", code=AssetCode.USD)
        )

        found = await BubbleReader(uow).get_all()

        assert [c.bubble_id for c in found] == [gold.id, dollar.id]
        assert {c.code for c in found} == {AssetCode.GOLD18, AssetCode.USD}

    async def test_the_context_carries_the_aggregation_rule(
        self, uow: PGUnitOfWork
    ) -> None:
        bubbles, configs = _bubbles(uow)
        created = await bubbles.create(
            BubbleCreate(title="حباب طلا", code=AssetCode.GOLD18)
        )
        await configs.update(
            created.id,
            BubbleConfigUpdate(agg_type=AggregationType.MEAN),
        )

        found = await BubbleReader(uow).get_all()

        assert found[0].config.agg_type == AggregationType.MEAN

    async def test_get_all_on_an_empty_table(self, uow: PGUnitOfWork) -> None:
        found = await BubbleReader(uow).get_all()

        assert list(found) == []


@pytest.mark.usefixtures("migrated_test_db", "clean_db")
class TestSwitchOrderReader:
    async def test_it_reads_the_order_a_market_is_tried_in(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)
        await _switch(uow, asset, SourceSwitch.SUPPLIER, 1)
        await _switch(uow, asset, SourceSwitch.IRAN_MARKET, 0)

        found = await SwitchOrderReader(uow).get_switch_order(asset.id)

        assert [c.switch for c in found] == [
            SourceSwitch.IRAN_MARKET,
            SourceSwitch.SUPPLIER,
        ]
        assert [c.order for c in found] == [0, 1]
        assert found[0].code == AssetCode.GOLD18
        assert found[0].asset_id == asset.id

    async def test_two_markets_may_share_a_level(
        self, uow: PGUnitOfWork
    ) -> None:
        # a shared level still has to read back in a stable order
        asset = await _asset(uow)
        await _switch(uow, asset, SourceSwitch.IRAN_MARKET, 0)
        await _switch(uow, asset, SourceSwitch.SUPPLIER, 0)

        found = await SwitchOrderReader(uow).get_switch_order(asset.id)

        assert [c.switch for c in found] == [
            SourceSwitch.IRAN_MARKET,
            SourceSwitch.SUPPLIER,
        ]

    async def test_an_asset_with_no_market_switched_on(
        self, uow: PGUnitOfWork
    ) -> None:
        asset = await _asset(uow)

        found = await SwitchOrderReader(uow).get_switch_order(asset.id)

        assert list(found) == []

    async def test_the_order_of_one_asset_is_not_another_s(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await _switch(uow, gold, SourceSwitch.SUPPLIER, 0)
        await _switch(uow, dollar, SourceSwitch.IRAN_MARKET, 0)

        found = await SwitchOrderReader(uow).get_switch_order(dollar.id)

        assert [c.switch for c in found] == [SourceSwitch.IRAN_MARKET]
        assert found[0].code == AssetCode.USD

    async def test_get_all_groups_every_asset_by_its_own_order(
        self, uow: PGUnitOfWork
    ) -> None:
        gold = await _asset(uow)
        dollar = await _asset(uow, AssetCode.USD)
        await _switch(uow, gold, SourceSwitch.GLOBAL_MARKET, 2)
        await _switch(uow, gold, SourceSwitch.IRAN_MARKET, 0)
        await _switch(uow, dollar, SourceSwitch.IRAN_MARKET, 1)

        found = await SwitchOrderReader(uow).get_all()

        assert [(c.asset_id, c.switch) for c in found] == [
            (gold.id, SourceSwitch.IRAN_MARKET),
            (gold.id, SourceSwitch.GLOBAL_MARKET),
            (dollar.id, SourceSwitch.IRAN_MARKET),
        ]

    async def test_get_all_on_an_empty_table(self, uow: PGUnitOfWork) -> None:
        found = await SwitchOrderReader(uow).get_all()

        assert list(found) == []
