from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from src.common.bases.schemas import BaseMeta, PagerMeta
from src.modules.price.sources.config.dependencies import SourceID
from src.modules.price.sources.domain.dtos import (
    SourceConfigUpdate,
    SourceCreate,
    SourceSearch,
    SourceUpdate,
)
from src.modules.price.sources.domain.enums import SourceSwitch
from src.modules.price.sources.domain.schemas import (
    SourceConfigOut,
    SourceOut,
    SourceWithConfigOut,
)
from src.modules.price.sources.interfaces import (
    ISourceConfigService,
    ISourceService,
)
from src.web.response import APIResponse

# open until the auth module lands and brings the guard with it
router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
    route_class=DishkaRoute,
)

SourceResponse = APIResponse[SourceOut, None]
PagedSourceResponse = APIResponse[SourceOut, BaseMeta]
SourceWithConfigResponse = APIResponse[SourceWithConfigOut, None]
SourceConfigResponse = APIResponse[SourceConfigOut, None]


@router.post(
    "", response_model=SourceResponse, response_model_exclude_defaults=True
)
async def create_source(
    data: SourceCreate,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    """
    Desc: Create a source together with its default config.
    Args:
        data (SourceCreate): Validated payload to persist.
        service (ISourceService): The source service.
    Returns:
        return (SourceResponse): The created source.
    """
    source = await service.create(data)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.get(
    "", response_model=SourceResponse, response_model_exclude_defaults=True
)
async def get_sources(
    service: FromDishka[ISourceService],
) -> SourceResponse:
    """
    Desc: Get every source.
    Args:
        service (ISourceService): The source service.
    Returns:
        return (SourceResponse): All sources.
    """
    sources = await service.get_all()
    return APIResponse.from_data(SourceOut.from_objs(sources))


@router.get(
    "/search",
    response_model=PagedSourceResponse,
    response_model_exclude_defaults=True,
)
async def search_sources(
    data: Annotated[SourceSearch, Query()],
    service: FromDishka[ISourceService],
) -> PagedSourceResponse:
    """
    Desc: Get a filtered page of sources.
    Args:
        data (SourceSearch): Free text, market filters and paging.
        service (ISourceService): The source service.
    Returns:
        return (PagedSourceResponse): The page of sources and its pager.
    """
    paged = await service.get_page(data)
    return APIResponse(
        success=True,
        data=SourceOut.from_objs(paged.items),
        meta=BaseMeta(
            pager=PagerMeta.from_total(
                data.page, data.per_page, paged.total_items
            )
        ),
    )


@router.get(
    "/configs",
    response_model=SourceWithConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_sources_with_config(
    service: FromDishka[ISourceService],
    switch: SourceSwitch | None = None,
) -> SourceWithConfigResponse:
    """
    Desc: Get sources with their configs, optionally one market's only.
    Args:
        service (ISourceService): The source service.
        switch (SourceSwitch | None): The market to narrow to, if any.
    Returns:
        return (SourceWithConfigResponse): Each source with its config.
    """
    if switch is None:
        sources = await service.get_all_with_config()
    else:
        sources = await service.get_by_switch_with_config(switch)
    return APIResponse.from_data(SourceWithConfigOut.from_objs(sources))


@router.get(
    "/{id:int}",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def get_source(
    id: SourceID,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    """
    Desc: Get a source by id.
    Args:
        id (int): ID of the source.
        service (ISourceService): The source service.
    Returns:
        return (SourceResponse): The found source.
    """
    source = await service.get_by_id(id)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.patch(
    "/{id:int}",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def update_source(
    id: SourceID,
    data: SourceUpdate,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    """
    Desc: Patch a source by id.
    Args:
        id (int): ID of the source.
        data (SourceUpdate): The fields to change.
        service (ISourceService): The source service.
    Returns:
        return (SourceResponse): The updated source.
    """
    source = await service.update(id, data)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.delete(
    "/{id:int}",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def remove_source(
    id: SourceID,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    """
    Desc: Delete a source by id, its config cascading with it.
    Args:
        id (int): ID of the source.
        service (ISourceService): The source service.
    Returns:
        return (SourceResponse): The deleted source.
    """
    source = await service.remove(id)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.delete(
    "/{id:int}/error",
    response_model=SourceResponse,
    response_model_exclude_defaults=True,
)
async def clear_source_error(
    id: SourceID,
    service: FromDishka[ISourceService],
) -> SourceResponse:
    """
    Desc: Clear a source's recorded error.
    Args:
        id (int): ID of the source.
        service (ISourceService): The source service.
    Returns:
        return (SourceResponse): The updated source.
    """
    source = await service.clear_error(id)
    return APIResponse.from_data(SourceOut.from_obj(source))


@router.get(
    "/{id:int}/config",
    response_model=SourceConfigResponse,
    response_model_exclude_defaults=True,
)
async def get_source_config(
    id: SourceID,
    service: FromDishka[ISourceConfigService],
) -> SourceConfigResponse:
    """
    Desc: Get a source's config.
    Args:
        id (int): ID of the source.
        service (ISourceConfigService): The source config service.
    Returns:
        return (SourceConfigResponse): The found config.
    """
    config = await service.get_by_source_id(id)
    return APIResponse.from_data(SourceConfigOut.from_obj(config))


@router.patch(
    "/{id:int}/config",
    response_model=SourceConfigResponse,
    response_model_exclude_defaults=True,
)
async def update_source_config(
    id: SourceID,
    data: SourceConfigUpdate,
    service: FromDishka[ISourceConfigService],
) -> SourceConfigResponse:
    """
    Desc: Patch a source's config.
    Args:
        id (int): ID of the source.
        data (SourceConfigUpdate): The fields to change.
        service (ISourceConfigService): The source config service.
    Returns:
        return (SourceConfigResponse): The updated config.
    """
    config = await service.update(id, data)
    return APIResponse.from_data(SourceConfigOut.from_obj(config))
