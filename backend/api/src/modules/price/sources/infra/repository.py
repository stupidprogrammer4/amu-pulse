from typing import Any, Optional, Sequence

from sqlalchemy import ColumnElement, update
from sqlalchemy.orm import joinedload
from sqlmodel import col, select

from src.common.bases.results import PagedType
from src.infra.postgres.repository.base import (
    PGIDRepository,
    PGTimestampRepository,
)
from src.modules.price.sources.domain.enums import (
    SourceSwitch,
)
from src.modules.price.sources.domain.models import (
    SourceConfigModel,
    SourceModel,
)


class SourceRepository(PGIDRepository[SourceModel]):
    async def get_page(
        self,
        q: str | None,
        source_types: Sequence[SourceSwitch] | None,
        has_error: bool | None,
        offset: int,
        limit: int,
        id_match: int | None = None,
    ) -> PagedType[SourceModel]:
        """
        Desc: Get a filtered page of sources, newest first, with its count.
        Args:
            q (str | None): Free text over title and code.
            source_types (Sequence[SourceSwitch] | None): Markets to narrow
                to; the front end offers them as checkboxes.
            has_error (bool | None): Whether to keep only failing sources.
            offset (int): Rows to skip.
            limit (int): Page size.
            id_match (int | None): Internal id a numeric query decoded to.
        Returns:
            return (PagedType[SourceModel]): The page and the total count.
        """
        clauses: list[ColumnElement[bool]] = []
        if q is not None:
            pattern = f"%{q}%"
            clause = col(SourceModel.title).ilike(pattern) | col(
                SourceModel.code
            ).ilike(pattern)
            if id_match is not None:
                clause = clause | (col(SourceModel.id) == id_match)
            clauses.append(clause)
        if source_types:
            clauses.append(col(SourceModel.source_type).in_(source_types))
        if has_error is not None:
            clauses.append(
                col(SourceModel.error).isnot(None)
                if has_error
                else col(SourceModel.error).is_(None)
            )
        stmt = (
            select(SourceModel)
            .where(*clauses)
            .order_by(col(SourceModel.id).desc())
        )
        paged = await self._paginate(stmt, offset, limit)
        return paged

    async def get_all_with_config(self) -> Sequence[SourceModel]:
        """
        Desc: Get every source with its config eagerly loaded, oldest first.
        Returns:
            return (Sequence[SourceModel]): All sources, each carrying its
                config.
        """
        stmt = (
            select(SourceModel)
            .options(joinedload(SourceModel.config, innerjoin=True))
            .order_by(col(SourceModel.id))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def get_by_switch_with_config(
        self,
        switch: SourceSwitch,
    ) -> Sequence[SourceModel]:
        """
        Desc: Get one market's sources with their configs, oldest first.
        Args:
            switch (SourceSwitch): The market the sources feed.
        Returns:
            return (Sequence[SourceModel]): The market's sources, each
                carrying its config.
        """
        stmt = (
            select(SourceModel)
            .options(joinedload(SourceModel.config, innerjoin=True))
            .where(col(SourceModel.source_type) == switch)
            .order_by(col(SourceModel.id))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def bulk_update(
        self,
        rows: Sequence[SourceModel],
    ) -> Sequence[SourceModel]:
        """
        Desc: Write each given source's own columns in one statement.
        Args:
            rows (Sequence[SourceModel]): The sources to write.
        Returns:
            return (Sequence[SourceModel]): The written sources.
        """
        stmt = self._bulk_update_stmt(rows, col(SourceModel.id))
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SourceConfigRepository(PGTimestampRepository[SourceConfigModel]):
    async def get_by_source_id(
        self,
        source_id: int,
    ) -> Optional[SourceConfigModel]:
        """
        Desc: Get a source's config by the source it belongs to.
        Args:
            source_id (int): ID of the owning source.
        Returns:
            return (Optional[SourceConfigModel]): Found config or None.
        """
        stmt = select(SourceConfigModel).where(
            col(SourceConfigModel.source_id) == source_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_source_id(
        self,
        source_id: int,
        row: dict[str, Any],
    ) -> Optional[SourceConfigModel]:
        """
        Desc: Patch a source's config from a column dict.
        Args:
            source_id (int): ID of the owning source.
            row (dict[str, Any]): Column values to write.
        Returns:
            return (Optional[SourceConfigModel]): Updated config or None.
        """
        stmt = (
            update(SourceConfigModel)
            .where(col(SourceConfigModel.source_id) == source_id)
            .values(**row)
            .returning(SourceConfigModel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
