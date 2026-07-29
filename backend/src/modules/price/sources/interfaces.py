from typing import Protocol, Sequence

from src.common.bases.results import PagedType
from src.modules.price.sources.domain.dtos import (
    SourceConfigUpdate,
    SourceCreate,
    SourceSearch,
    SourceUpdate,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.errors import SourceErrorInfo
from src.modules.price.sources.domain.models import (
    SourceConfigModel,
    SourceModel,
)


class ISourceConfigService(Protocol):
    async def create_default(self, source_id: int) -> SourceConfigModel:
        """
        Desc: Create the default config of a newly created source.
        Args:
            source_id (int): ID of the owning source.
        Returns:
            return (SourceConfigModel): The created config.
        """
        ...

    async def update(
        self,
        source_id: int,
        data: SourceConfigUpdate,
    ) -> SourceConfigModel:
        """
        Desc: Patch a source's config.
        Args:
            source_id (int): ID of the owning source.
            data (SourceConfigUpdate): The fields to change.
        Returns:
            return (SourceConfigModel): The updated config.
        """
        ...

    async def get_by_source_id(self, source_id: int) -> SourceConfigModel:
        """
        Desc: Get a source's config.
        Args:
            source_id (int): ID of the owning source.
        Returns:
            return (SourceConfigModel): The found config.
        """
        ...

    async def get_all(self) -> Sequence[SourceConfigModel]:
        """
        Desc: Get every source config.
        Returns:
            return (Sequence[SourceConfigModel]): All configs.
        """
        ...


class ISourceService(Protocol):
    async def create(self, data: SourceCreate) -> SourceModel:
        """
        Desc: Create a source together with its default config.
        Args:
            data (SourceCreate): Validated payload to persist.
        Returns:
            return (SourceModel): The created source.
        """
        ...

    async def update(self, id: int, data: SourceUpdate) -> SourceModel:
        """
        Desc: Patch a source by id.
        Args:
            id (int): ID of the source.
            data (SourceUpdate): The fields to change.
        Returns:
            return (SourceModel): The updated source.
        """
        ...

    async def get_by_id(self, id: int) -> SourceModel:
        """
        Desc: Get a source by id.
        Args:
            id (int): ID of the source.
        Returns:
            return (SourceModel): The found source.
        """
        ...

    async def get_all(self) -> Sequence[SourceModel]:
        """
        Desc: Get every source.
        Returns:
            return (Sequence[SourceModel]): All sources.
        """
        ...

    async def get_page(self, data: SourceSearch) -> PagedType[SourceModel]:
        """
        Desc: Get a filtered page of sources.
        Args:
            data (SourceSearch): Free text, market filters and paging.
        Returns:
            return (PagedType[SourceModel]): The page and the total count.
        """
        ...

    async def get_all_with_config(self) -> Sequence[SourceModel]:
        """
        Desc: Get every source with its config eagerly loaded.
        Returns:
            return (Sequence[SourceModel]): All sources, each carrying its
                config.
        """
        ...

    async def get_by_switch_with_config(
        self,
        switch: SourceSwitch,
    ) -> Sequence[SourceModel]:
        """
        Desc: Get one market's sources with their configs.
        Args:
            switch (SourceSwitch): The market the sources feed.
        Returns:
            return (Sequence[SourceModel]): The market's sources, each
                carrying its config.
        """
        ...

    async def mark_failed(
        self,
        id: int,
        error: SourceErrorInfo,
    ) -> SourceModel:
        """
        Desc: Record why a source's last fetch failed.
        Args:
            id (int): ID of the source.
            error (SourceErrorInfo): What went wrong.
        Returns:
            return (SourceModel): The updated source.
        """
        ...

    async def clear_error(self, id: int) -> SourceModel:
        """
        Desc: Clear a source's recorded error once it answers again.
        Args:
            id (int): ID of the source.
        Returns:
            return (SourceModel): The updated source.
        """
        ...

    async def remove(self, id: int) -> SourceModel:
        """
        Desc: Delete a source by id, its config cascading with it.
        Args:
            id (int): ID of the source.
        Returns:
            return (SourceModel): The deleted source.
        """
        ...
