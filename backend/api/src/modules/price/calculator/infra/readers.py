from typing import Optional, Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGReader
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.models import (
    AssetConfigModel,
    AssetModel,
    AssetSwitchModel,
)
from src.modules.price.bubbles.domain.models import (
    BubbleConfigModel,
    BubbleModel,
)
from src.modules.price.calculator.domain.context import (
    AssetContext,
    BubbleContext,
    SwitchOrderContext,
    SymbolContext,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.models import SourceModel
from src.modules.price.symbols.domain.enums import SymbolCode
from src.modules.price.symbols.domain.models import SymbolModel


class SymbolReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def get_all(
        self,
        excludes: Sequence[AssetCode] = (),
    ) -> Sequence[SymbolContext]:
        """
        Desc: Read every symbol with the asset it is quoted for, oldest
        first.
        Args:
            excludes (Sequence[AssetCode]): The assets to leave out.
        Returns:
            return (Sequence[SymbolContext]): The lines a sweep folds into
                asset prices.
        """
        stmt = (
            select(SymbolModel, AssetModel.code)
            .join(AssetModel, col(AssetModel.id) == col(SymbolModel.asset_id))
            .where(col(AssetModel.code).not_in(excludes))
            .order_by(col(SymbolModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            SymbolContext(
                id=symbol.id,
                code=AssetCode(code),
                symbol=SymbolCode(symbol.code),
                asset_id=symbol.asset_id,
            )
            for symbol, code in rows
        ]

    async def get_symbols_of_asset(
        self,
        asset_id: int,
    ) -> Sequence[SymbolContext]:
        """
        Desc: Read one asset's symbols, oldest first.
        Args:
            asset_id (int): ID of the asset being priced.
        Returns:
            return (Sequence[SymbolContext]): The lines that asset is
                quoted through, empty when it has none.
        """
        stmt = (
            select(SymbolModel, AssetModel.code)
            .join(AssetModel, col(AssetModel.id) == col(SymbolModel.asset_id))
            .where(col(SymbolModel.asset_id) == asset_id)
            .order_by(col(SymbolModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            SymbolContext(
                id=symbol.id,
                code=AssetCode(code),
                symbol=SymbolCode(symbol.code),
                asset_id=symbol.asset_id,
            )
            for symbol, code in rows
        ]


class AssetReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def get_all_config(
        self,
        excludes: Sequence[AssetCode] = (),
    ) -> Sequence[AssetContext]:
        """
        Desc: Read every asset and its config, oldest first.
        Args:
            excludes (Sequence[AssetCode]): The assets to leave out.
        Returns:
            return (Sequence[AssetContext]): The assets a sweep prices, each
                carrying the rule its readings are folded by.
        """
        stmt = (
            select(AssetModel, AssetConfigModel)
            .join(
                AssetConfigModel,
                col(AssetConfigModel.asset_id) == col(AssetModel.id),
            )
            .where(col(AssetModel.code).not_in(excludes))
            .order_by(col(AssetModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            AssetContext(
                code=AssetCode(asset.code),
                asset_id=asset.id,
                config=cfg,
            )
            for asset, cfg in rows
        ]

    async def get_id_by_code(self, code: AssetCode) -> Optional[int]:
        """
        Desc: Read the id the given asset code belongs to.
        Args:
            code (AssetCode): Code of the asset.
        Returns:
            return (Optional[int]): Its id, or None when no asset carries
                that code.
        """
        stmt = select(AssetModel.id).where(col(AssetModel.code) == code)
        result = await self.session.execute(stmt)
        found = result.scalar_one_or_none()
        return found

    async def get_asset_config(
        self,
        asset_id: int,
    ) -> Optional[AssetContext]:
        """
        Desc: Read one asset and its config.
        Args:
            asset_id (int): ID of the asset being priced.
        Returns:
            return (Optional[AssetContext]): The asset, or None when it has
                no row or no config.
        """
        stmt = (
            select(AssetModel, AssetConfigModel)
            .join(
                AssetConfigModel,
                col(AssetConfigModel.asset_id) == col(AssetModel.id),
            )
            .where(col(AssetModel.id) == asset_id)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        context = None
        if row is not None:
            asset, cfg = row
            context = AssetContext(
                code=AssetCode(asset.code),
                asset_id=asset.id,
                config=cfg,
            )
        return context


class BubbleReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def get_all(self) -> Sequence[BubbleContext]:
        """
        Desc: Read every bubble and its config, oldest first.
        Returns:
            return (Sequence[BubbleContext]): The premiums a sweep settles.
        """
        stmt = (
            select(BubbleModel, BubbleConfigModel)
            .join(
                BubbleConfigModel,
                col(BubbleConfigModel.bubble_id) == col(BubbleModel.id),
            )
            .order_by(col(BubbleModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            BubbleContext(
                code=AssetCode(bubble.code),
                bubble_id=bubble.id,
                config=cfg,
            )
            for bubble, cfg in rows
        ]

    async def get_bubble_config(
        self,
        bubble_id: int,
    ) -> Optional[BubbleContext]:
        """
        Desc: Read one bubble and its config.
        Args:
            bubble_id (int): ID of the bubble being settled.
        Returns:
            return (Optional[BubbleContext]): The bubble, or None when it
                has no row or no config.
        """
        stmt = (
            select(BubbleModel, BubbleConfigModel)
            .join(
                BubbleConfigModel,
                col(BubbleConfigModel.bubble_id) == col(BubbleModel.id),
            )
            .where(col(BubbleModel.id) == bubble_id)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        context = None
        if row is not None:
            bubble, cfg = row
            context = BubbleContext(
                code=AssetCode(bubble.code),
                bubble_id=bubble.id,
                config=cfg,
            )
        return context


class SwitchOrderReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def get_switch_order(
        self,
        asset_id: int,
    ) -> Sequence[SwitchOrderContext]:
        """
        Desc: Read one asset's markets, the one tried first at the front.
        Args:
            asset_id (int): ID of the asset being priced.
        Returns:
            return (Sequence[SwitchOrderContext]): The markets that price
                the asset, empty when no market is switched on for it.
        """
        stmt = (
            select(AssetSwitchModel, AssetModel.code)
            .join(
                AssetModel,
                col(AssetModel.id) == col(AssetSwitchModel.asset_id),
            )
            .where(col(AssetSwitchModel.asset_id) == asset_id)
            .order_by(
                col(AssetSwitchModel.priority),
                col(AssetSwitchModel.id),
            )
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            SwitchOrderContext(
                code=AssetCode(code),
                asset_id=switch.asset_id,
                switch=SourceSwitch(switch.switch),
                order=switch.priority,
            )
            for switch, code in rows
        ]

    async def get_all(
        self,
        excludes: Sequence[AssetCode] = (),
    ) -> Sequence[SwitchOrderContext]:
        """
        Desc: Read every asset's markets, each asset's own order kept.
        Args:
            excludes (Sequence[AssetCode]): The assets to leave out.
        Returns:
            return (Sequence[SwitchOrderContext]): The markets that price
                each asset, grouped by asset, the one tried first at the
                front of its group.
        """
        stmt = (
            select(AssetSwitchModel, AssetModel.code)
            .join(
                AssetModel,
                col(AssetModel.id) == col(AssetSwitchModel.asset_id),
            )
            .where(col(AssetModel.code).not_in(excludes))
            .order_by(
                col(AssetSwitchModel.asset_id),
                col(AssetSwitchModel.priority),
                col(AssetSwitchModel.id),
            )
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            SwitchOrderContext(
                code=AssetCode(code),
                asset_id=switch.asset_id,
                switch=SourceSwitch(switch.switch),
                order=switch.priority,
            )
            for switch, code in rows
        ]


class SourceReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def get_source_switches(
        self,
    ) -> Sequence[tuple[int, SourceSwitch]]:
        """
        Desc: Read which market each source feeds, oldest first.
        Returns:
            return (Sequence[tuple[int, SourceSwitch]]): Each source's id
                and market, enough to put a reading under the market it
                was quoted in.
        """
        stmt = select(SourceModel.id, SourceModel.source_type).order_by(
            col(SourceModel.id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [(id, SourceSwitch(switch)) for id, switch in rows]
