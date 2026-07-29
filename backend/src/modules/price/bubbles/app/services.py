from typing import Sequence

from src.common.bases.services import BaseIDService, BaseService
from src.modules.price.assets.domain.enums import AggregationType
from src.modules.price.bubbles.domain.dtos import (
    BubbleConfigUpdate,
    BubbleCreate,
    BubbleUpdate,
)
from src.modules.price.bubbles.domain.models import (
    BubbleConfigModel,
    BubbleModel,
)
from src.modules.price.bubbles.infra.repository import (
    BubbleConfigRepository,
    BubbleRepository,
)
from src.modules.price.bubbles.interfaces import IBubbleConfigService


class BubbleConfigService(BaseService[BubbleConfigModel]):
    # what a freshly created bubble polls with until an admin tunes it
    default_scheduler_on = True
    default_scheduler_seconds = 60
    # the median shrugs off one publisher printing nonsense; with a single
    # source every aggregation returns that source's reading
    default_agg_type = AggregationType.MEDIAN

    def __init__(self, repo: BubbleConfigRepository) -> None:
        """
        Desc: Build the service with its repository.
        Args:
            repo (BubbleConfigRepository): The bubble config repository.
        """
        self.repo = repo

    async def create_default(self, bubble_id: int) -> BubbleConfigModel:
        """
        Desc: Create the default config of a newly created bubble.
        Args:
            bubble_id (int): ID of the owning bubble.
        Returns:
            return (BubbleConfigModel): The created config.
        """
        config = await self.repo.create(
            BubbleConfigModel(
                bubble_id=bubble_id,
                scheduler_on=self.default_scheduler_on,
                scheduler_seconds=self.default_scheduler_seconds,
                agg_type=self.default_agg_type,
            )
        )
        return config

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
        row = self._check_not_empty_dict(data.to_row())
        config = await self.repo.update_by_bubble_id(bubble_id, row)
        config = self._check_for_existence("bubble_id", bubble_id, config)
        return config

    async def get_by_bubble_id(self, bubble_id: int) -> BubbleConfigModel:
        """
        Desc: Get a bubble's config.
        Args:
            bubble_id (int): ID of the owning bubble.
        Returns:
            return (BubbleConfigModel): The found config.
        """
        config = await self.repo.get_by_bubble_id(bubble_id)
        config = self._check_for_existence("bubble_id", bubble_id, config)
        return config

    async def get_all(self) -> Sequence[BubbleConfigModel]:
        """
        Desc: Get every bubble config.
        Returns:
            return (Sequence[BubbleConfigModel]): All configs.
        """
        configs = await self.repo.get_all()
        return configs


class BubbleService(BaseIDService[BubbleModel]):
    def __init__(
        self,
        repo: BubbleRepository,
        configs: IBubbleConfigService,
    ) -> None:
        """
        Desc: Build the service with its repository and the config service.
        Args:
            repo (BubbleRepository): The bubble repository.
            configs (IBubbleConfigService): The bubble config service.
        """
        self.repo = repo
        self.configs = configs

    async def create(self, data: BubbleCreate) -> BubbleModel:
        """
        Desc: Create a bubble together with its default config.
        Args:
            data (BubbleCreate): Validated payload to persist.
        Returns:
            return (BubbleModel): The created bubble.
        """
        bubble = await self.repo.create(
            BubbleModel(**data.to_row(exclude_unset=False))
        )
        await self.configs.create_default(bubble.id)
        return bubble

    async def update(self, id: int, data: BubbleUpdate) -> BubbleModel:
        """
        Desc: Patch a bubble by id.
        Args:
            id (int): ID of the bubble.
            data (BubbleUpdate): The fields to change.
        Returns:
            return (BubbleModel): The updated bubble.
        """
        row = self._check_not_empty_dict(data.to_row())
        bubble = await self.repo.update_by_id(id, row)
        bubble = self._check_for_id_existence(id, bubble)
        return bubble

    async def get_by_id(self, id: int) -> BubbleModel:
        """
        Desc: Get a bubble by id.
        Args:
            id (int): ID of the bubble.
        Returns:
            return (BubbleModel): The found bubble.
        """
        bubble = await self.repo.get_by_id(id)
        bubble = self._check_for_id_existence(id, bubble)
        return bubble

    async def get_all(self) -> Sequence[BubbleModel]:
        """
        Desc: Get every bubble.
        Returns:
            return (Sequence[BubbleModel]): All bubbles.
        """
        bubbles = await self.repo.get_all()
        return bubbles

    async def get_all_with_config(self) -> Sequence[BubbleModel]:
        """
        Desc: Get every bubble with its config eagerly loaded.
        Returns:
            return (Sequence[BubbleModel]): All bubbles, each carrying its
                config.
        """
        bubbles = await self.repo.get_all_with_config()
        return bubbles

    async def remove(self, id: int) -> BubbleModel:
        """
        Desc: Delete a bubble by id, its config cascading with it.
        Args:
            id (int): ID of the bubble.
        Returns:
            return (BubbleModel): The deleted bubble.
        """
        bubble = await self.repo.delete_by_id(id)
        bubble = self._check_for_id_existence(id, bubble)
        return bubble
