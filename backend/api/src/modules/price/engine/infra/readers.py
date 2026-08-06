from typing import Optional, Sequence

from sqlmodel import col, select

from src.infra.postgres.repository.base import PGReader
from src.infra.postgres.uow import PGUnitOfWork
from src.modules.price.assets.domain.models import AssetConfigModel, AssetModel
from src.modules.price.engine.domain.context import (
    AssetContext,
    AssetRefContext,
    SourceContext,
    SymbolRefContext,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.models import (
    SourceConfigModel,
    SourceModel,
)
from src.modules.price.symbols.domain.models import SymbolModel


class AssetReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)

    async def read_refs(self) -> Sequence[AssetRefContext]:
        stmt = select(AssetModel.id, AssetModel.code).order_by(
            col(AssetModel.id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [AssetRefContext(code=code, id=id) for id, code in rows]

    async def read_scheduled(self) -> Sequence[AssetContext]:
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
        super().__init__(uow)

    async def read_all(self) -> Sequence[SourceContext]:
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


class SymbolReader(PGReader):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)

    async def read_refs(self) -> Sequence[SymbolRefContext]:
        stmt = select(SymbolModel.id, SymbolModel.code).order_by(
            col(SymbolModel.id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [SymbolRefContext(code=code, id=id) for id, code in rows]
