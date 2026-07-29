from typing import Any, Optional, Sequence

from sqlalchemy import update
from sqlalchemy.orm import joinedload
from sqlmodel import col, select

from src.infra.postgres.repository.base import (
    PGIDRepository,
    PGTimestampRepository,
)
from src.modules.price.bubbles.domain.models import (
    BubbleConfigModel,
    BubbleModel,
)


class BubbleRepository(PGIDRepository[BubbleModel]):
    async def get_all_with_config(self) -> Sequence[BubbleModel]:
        """
        Desc: Get every bubble with its config eagerly loaded, oldest first.
        Returns:
            return (Sequence[BubbleModel]): All bubbles, each carrying its
                config.
        """
        stmt = (
            select(BubbleModel)
            .options(joinedload(BubbleModel.config, innerjoin=True))
            .order_by(col(BubbleModel.id))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()


class BubbleConfigRepository(PGTimestampRepository[BubbleConfigModel]):
    async def get_by_bubble_id(
        self,
        bubble_id: int,
    ) -> Optional[BubbleConfigModel]:
        """
        Desc: Get a bubble's config by the bubble it belongs to.
        Args:
            bubble_id (int): ID of the owning bubble.
        Returns:
            return (Optional[BubbleConfigModel]): Found config or None.
        """
        stmt = select(BubbleConfigModel).where(
            col(BubbleConfigModel.bubble_id) == bubble_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_bubble_id(
        self,
        bubble_id: int,
        row: dict[str, Any],
    ) -> Optional[BubbleConfigModel]:
        """
        Desc: Patch a bubble's config from a column dict.
        Args:
            bubble_id (int): ID of the owning bubble.
            row (dict[str, Any]): Column values to write.
        Returns:
            return (Optional[BubbleConfigModel]): Updated config or None.
        """
        stmt = (
            update(BubbleConfigModel)
            .where(col(BubbleConfigModel.bubble_id) == bubble_id)
            .values(**row)
            .returning(BubbleConfigModel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
