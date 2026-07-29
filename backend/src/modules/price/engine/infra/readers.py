from typing import Optional, Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGReader
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.domain.models import AssetConfigModel, AssetModel
from src.modules.price.engine.domain.context import (
    AssetContext,
    AssetRefContext,
    SourceContext,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.models import (
    SourceConfigModel,
    SourceModel,
)


class AssetReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def read_refs(self) -> Sequence[AssetRefContext]:
        """
        Desc: Read every asset's identity, oldest first.
        Returns:
            return (Sequence[AssetRefContext]): Each asset's code and id,
                enough to turn a quoted code into an asset_id.
        """
        stmt = select(AssetModel.id, AssetModel.code).order_by(
            col(AssetModel.id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [AssetRefContext(code=code, id=id) for id, code in rows]

    async def read_scheduled(self) -> Sequence[AssetContext]:
        """
        Desc: Read every asset whose scheduler is on, oldest first.
        Returns:
            return (Sequence[AssetContext]): The assets a sweep should price.
        """
        stmt = (
            select(AssetModel, AssetConfigModel)
            .join(
                AssetConfigModel,
                col(AssetConfigModel.asset_id) == col(AssetModel.id),
            )
            .where(col(AssetConfigModel.scheduler_on).is_(True))
            .order_by(col(AssetModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            AssetContext(code=asset.code, id=asset.id, cfg=cfg)
            for asset, cfg in rows
        ]

    async def read(self, asset_id: int) -> Optional[AssetContext]:
        """
        Desc: Read one asset and its config, whatever its scheduler says.
        Args:
            asset_id (int): ID of the asset to price.
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
            context = AssetContext(code=asset.code, id=asset.id, cfg=cfg)
        return context


class SourceReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        """
        Desc: Build the reader over the unit of work.
        Args:
            uow (PGUnitOfWork): Unit of work whose session runs the query.
        """
        super().__init__(uow)

    async def read_all(self) -> Sequence[SourceContext]:
        """
        Desc: Read every source and its config, oldest first.
        Returns:
            return (Sequence[SourceContext]): Every source the engine may
                fetch from.
        """
        stmt = (
            select(SourceModel, SourceConfigModel)
            .join(
                SourceConfigModel,
                col(SourceConfigModel.source_id) == col(SourceModel.id),
            )
            .order_by(col(SourceModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            SourceContext(
                code=source.code,
                id=source.id,
                switch=source.source_type,
                cfg=cfg,
            )
            for source, cfg in rows
        ]

    async def read_by_switch(
        self,
        switch: SourceSwitch,
    ) -> Sequence[SourceContext]:
        """
        Desc: Read one market's sources and their configs, oldest first.
        Args:
            switch (SourceSwitch): The market feeding the asset being priced.
        Returns:
            return (Sequence[SourceContext]): That market's sources.
        """
        stmt = (
            select(SourceModel, SourceConfigModel)
            .join(
                SourceConfigModel,
                col(SourceConfigModel.source_id) == col(SourceModel.id),
            )
            .where(col(SourceModel.source_type) == switch)
            .order_by(col(SourceModel.id))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            SourceContext(
                code=source.code,
                id=source.id,
                switch=source.source_type,
                cfg=cfg,
            )
            for source, cfg in rows
        ]
