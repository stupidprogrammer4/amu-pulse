from typing import Protocol, Sequence

from src.modules.price.bubbles.domain.dtos import (
    BubbleConfigUpdate,
    BubbleCreate,
    BubbleUpdate,
)
from src.modules.price.bubbles.domain.models import (
    BubbleConfigModel,
    BubbleModel,
)


class IBubbleConfigService(Protocol):
    async def create_default(self, bubble_id: int) -> BubbleConfigModel:
        """
        Desc: Create the default config of a newly created bubble.
        Args:
            bubble_id (int): ID of the owning bubble.
        Returns:
            return (BubbleConfigModel): The created config.
        """
        ...

    async def update(
        self,
        bubble_id: int,
        data: BubbleConfigUpdate,
    ) -> BubbleConfigModel:
        """
        Desc: Patch a bubble's config.
        Args:
            bubble_id (int): ID of the owning bubble.
            data (BubbleConfigUpdate): The fields to change.
        Returns:
            return (BubbleConfigModel): The updated config.
        """
        ...

    async def get_by_bubble_id(self, bubble_id: int) -> BubbleConfigModel:
        """
        Desc: Get a bubble's config.
        Args:
            bubble_id (int): ID of the owning bubble.
        Returns:
            return (BubbleConfigModel): The found config.
        """
        ...

    async def get_all(self) -> Sequence[BubbleConfigModel]:
        """
        Desc: Get every bubble config.
        Returns:
            return (Sequence[BubbleConfigModel]): All configs.
        """
        ...


class IBubbleService(Protocol):
    async def create(self, data: BubbleCreate) -> BubbleModel:
        """
        Desc: Create a bubble together with its default config.
        Args:
            data (BubbleCreate): Validated payload to persist.
        Returns:
            return (BubbleModel): The created bubble.
        """
        ...

    async def update(self, id: int, data: BubbleUpdate) -> BubbleModel:
        """
        Desc: Patch a bubble by id.
        Args:
            id (int): ID of the bubble.
            data (BubbleUpdate): The fields to change.
        Returns:
            return (BubbleModel): The updated bubble.
        """
        ...

    async def get_by_id(self, id: int) -> BubbleModel:
        """
        Desc: Get a bubble by id.
        Args:
            id (int): ID of the bubble.
        Returns:
            return (BubbleModel): The found bubble.
        """
        ...

    async def get_all(self) -> Sequence[BubbleModel]:
        """
        Desc: Get every bubble.
        Returns:
            return (Sequence[BubbleModel]): All bubbles.
        """
        ...

    async def get_all_with_config(self) -> Sequence[BubbleModel]:
        """
        Desc: Get every bubble with its config eagerly loaded.
        Returns:
            return (Sequence[BubbleModel]): All bubbles, each carrying its
                config.
        """
        ...

    async def remove(self, id: int) -> BubbleModel:
        """
        Desc: Delete a bubble by id, its config cascading with it.
        Args:
            id (int): ID of the bubble.
        Returns:
            return (BubbleModel): The deleted bubble.
        """
        ...
