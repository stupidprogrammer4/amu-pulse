from typing import Mapping, Sequence

from src.common.bases.results import PagedType
from src.common.bases.services import BaseIDService, BaseService
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
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
from src.modules.price.sources.infra.repository import (
    SourceConfigRepository,
    SourceRepository,
)
from src.modules.price.sources.interfaces import ISourceConfigService


class SourceConfigService(BaseService[SourceConfigModel]):
    # what a freshly created source fetches with until an admin tunes it
    default_timeout = 10

    def __init__(self, repo: SourceConfigRepository) -> None:
        """
        Desc: Build the service with its repository.
        Args:
            repo (SourceConfigRepository): The source config repository.
        """
        self.repo = repo

    async def create_default(self, source_id: int) -> SourceConfigModel:
        """
        Desc: Create the default config of a newly created source.
        Args:
            source_id (int): ID of the owning source.
        Returns:
            return (SourceConfigModel): The created config.
        """
        config = await self.repo.create(
            SourceConfigModel(
                source_id=source_id,
                timeout=self.default_timeout,
            )
        )
        return config

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
        row = self._check_not_empty_dict(data.to_row())
        config = await self.repo.update_by_source_id(source_id, row)
        config = self._check_for_existence("source_id", source_id, config)
        return config

    async def get_by_source_id(self, source_id: int) -> SourceConfigModel:
        """
        Desc: Get a source's config.
        Args:
            source_id (int): ID of the owning source.
        Returns:
            return (SourceConfigModel): The found config.
        """
        config = await self.repo.get_by_source_id(source_id)
        config = self._check_for_existence("source_id", source_id, config)
        return config

    async def get_all(self) -> Sequence[SourceConfigModel]:
        """
        Desc: Get every source config.
        Returns:
            return (Sequence[SourceConfigModel]): All configs.
        """
        configs = await self.repo.get_all()
        return configs


class SourceService(BaseIDService[SourceModel]):
    def __init__(
        self,
        repo: SourceRepository,
        configs: ISourceConfigService,
    ) -> None:
        """
        Desc: Build the service with its repository and the config service.
        Args:
            repo (SourceRepository): The source repository.
            configs (ISourceConfigService): The source config service.
        """
        self.repo = repo
        self.configs = configs

    async def create(self, data: SourceCreate) -> SourceModel:
        """
        Desc: Create a source together with its default config.
        Args:
            data (SourceCreate): Validated payload to persist.
        Returns:
            return (SourceModel): The created source.
        """
        source = await self.repo.create(
            SourceModel(**data.to_row(exclude_unset=False))
        )
        await self.configs.create_default(source.id)
        return source

    async def update(self, id: int, data: SourceUpdate) -> SourceModel:
        """
        Desc: Patch a source by id.
        Args:
            id (int): ID of the source.
            data (SourceUpdate): The fields to change.
        Returns:
            return (SourceModel): The updated source.
        """
        row = self._check_not_empty_dict(data.to_row())
        source = await self.repo.update_by_id(id, row)
        source = self._check_for_id_existence(id, source)
        return source

    async def get_by_id(self, id: int) -> SourceModel:
        """
        Desc: Get a source by id.
        Args:
            id (int): ID of the source.
        Returns:
            return (SourceModel): The found source.
        """
        source = await self.repo.get_by_id(id)
        source = self._check_for_id_existence(id, source)
        return source

    async def get_by_ids(
        self,
        ids: list[int],
    ) -> Sequence[SourceModel]:
        """
        Desc: Get the sources the given ids belong to.
        Args:
            ids (list[int]): IDs of the sources to read.
        Returns:
            return (Sequence[SourceModel]): The sources that exist.
        """
        sources = await self.repo.get_by_ids(ids)
        return sources

    async def get_all(self) -> Sequence[SourceModel]:
        """
        Desc: Get every source.
        Returns:
            return (Sequence[SourceModel]): All sources.
        """
        sources = await self.repo.get_all()
        return sources

    async def get_page(self, data: SourceSearch) -> PagedType[SourceModel]:
        """
        Desc: Get a filtered page of sources.
        Args:
            data (SourceSearch): Free text, market filters and paging.
        Returns:
            return (PagedType[SourceModel]): The page and the total count.
        """
        # an admin pastes a public id into the search box; match it as an id
        # too, not only as text
        id_match = None
        if data.q is not None and data.q.isdigit():
            id_match = SOURCE_ID_ENCRYPTION.try_decode(int(data.q))
        paged = await self.repo.get_page(
            q=data.q,
            source_types=data.source_types,
            has_error=data.has_error,
            offset=(data.page - 1) * data.per_page,
            limit=data.per_page,
            id_match=id_match,
        )
        return paged

    async def get_all_with_config(self) -> Sequence[SourceModel]:
        """
        Desc: Get every source with its config eagerly loaded.
        Returns:
            return (Sequence[SourceModel]): All sources, each carrying its
                config.
        """
        sources = await self.repo.get_all_with_config()
        return sources

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
        sources = await self.repo.get_by_switch_with_config(switch)
        return sources

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
        source = await self.repo.update_by_id(id, {"error": error})
        source = self._check_for_id_existence(id, source)
        return source

    async def clear_error(self, id: int) -> SourceModel:
        """
        Desc: Clear a source's recorded error once it answers again.
        Args:
            id (int): ID of the source.
        Returns:
            return (SourceModel): The updated source.
        """
        source = await self.repo.update_by_id(id, {"error": None})
        source = self._check_for_id_existence(id, source)
        return source

    async def remove(self, id: int) -> SourceModel:
        """
        Desc: Delete a source by id, its config cascading with it.
        Args:
            id (int): ID of the source.
        Returns:
            return (SourceModel): The deleted source.
        """
        source = await self.repo.delete_by_id(id)
        source = self._check_for_id_existence(id, source)
        return source


class SourceErrorService(BaseIDService[SourceModel]):
    def __init__(self, repo: SourceRepository) -> None:
        """
        Desc: Build the service with its repository.
        Args:
            repo (SourceRepository): The source repository.
        """
        self.repo = repo

    async def apply_errors(
        self,
        errors: Mapping[int, SourceErrorInfo | None],
    ) -> Sequence[SourceModel]:
        """
        Desc: Record what a crawl learned about every source it called.
        Args:
            errors (Mapping[int, SourceErrorInfo | None]): The failure of
                each source, or None where it answered.
        Returns:
            return (Sequence[SourceModel]): The updated sources.
        """
        rows = self._check_not_empty_dict(dict(errors))
        sources = await self.repo.bulk_update(
            [SourceModel(id=id, error=error) for id, error in rows.items()]
        )
        return sources
