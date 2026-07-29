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
    async def create_default(self, bubble_id: int) -> BubbleConfigModel: ...

    async def update(
        self,
        bubble_id: int,
        data: BubbleConfigUpdate,
    ) -> BubbleConfigModel: ...

    async def get_by_bubble_id(self, bubble_id: int) -> BubbleConfigModel: ...

    async def get_all(self) -> Sequence[BubbleConfigModel]: ...


class IBubbleService(Protocol):
    async def create(self, data: BubbleCreate) -> BubbleModel: ...

    async def update(self, id: int, data: BubbleUpdate) -> BubbleModel: ...

    async def get_by_id(self, id: int) -> BubbleModel: ...

    async def get_all(self) -> Sequence[BubbleModel]: ...

    async def get_all_with_config(self) -> Sequence[BubbleModel]: ...

    async def remove(self, id: int) -> BubbleModel: ...
