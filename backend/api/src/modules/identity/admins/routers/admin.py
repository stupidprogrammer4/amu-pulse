from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from src.common.bases.schemas import BaseMeta, PagerMeta
from src.modules.identity.admins.config.dependencies import AdminID
from src.modules.identity.admins.domain.dtos import (
    AdminCreate,
    AdminSearch,
    AdminSetPassword,
    AdminSetUsername,
    AdminUpdate,
)
from src.modules.identity.admins.domain.schemas import AdminOut
from src.modules.identity.admins.interfaces import IAdminService
from src.modules.identity.auth.config.dependencies import (
    super_admin_required,
)
from src.web.response import APIResponse

# managing admins is a super admin's job; every route below is guarded
router = APIRouter(
    prefix="/admins",
    tags=["Admins"],
    route_class=DishkaRoute,
    dependencies=[super_admin_required],
)

AdminResponse = APIResponse[AdminOut, None]
PagedAdminResponse = APIResponse[AdminOut, BaseMeta]


@router.post(
    "", response_model=AdminResponse, response_model_exclude_defaults=True
)
async def create_admin(
    data: AdminCreate,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.create(data)
    return APIResponse.from_data(AdminOut.from_obj(admin))


# before /{id:int}, or the router reads "search" as a malformed id
@router.get(
    "/search",
    response_model=PagedAdminResponse,
    response_model_exclude_defaults=True,
)
async def search_admins(
    data: Annotated[AdminSearch, Query()],
    service: FromDishka[IAdminService],
) -> PagedAdminResponse:
    paged = await service.get_paged(data)
    return APIResponse(
        success=True,
        data=AdminOut.from_objs(paged.items),
        meta=BaseMeta(
            pager=PagerMeta.from_total(
                data.page, data.per_page, paged.total_items
            )
        ),
    )


@router.get(
    "/{id:int}",
    response_model=AdminResponse,
    response_model_exclude_defaults=True,
)
async def get_admin(
    id: AdminID,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.get_by_id(id)
    return APIResponse.from_data(AdminOut.from_obj(admin))


@router.patch(
    "/{id:int}",
    response_model=AdminResponse,
    response_model_exclude_defaults=True,
)
async def update_admin(
    id: AdminID,
    data: AdminUpdate,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.update(id, data)
    return APIResponse.from_data(AdminOut.from_obj(admin))


# a credential each, on its own route: changing one is an event worth
# reading in a log, not a field patched in passing
@router.patch(
    "/{id:int}/username",
    response_model=AdminResponse,
    response_model_exclude_defaults=True,
)
async def set_admin_username(
    id: AdminID,
    data: AdminSetUsername,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.set_username(id, data.username)
    return APIResponse.from_data(AdminOut.from_obj(admin))


@router.patch(
    "/{id:int}/password",
    response_model=AdminResponse,
    response_model_exclude_defaults=True,
)
async def set_admin_password(
    id: AdminID,
    data: AdminSetPassword,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.set_password(id, data.password)
    return APIResponse.from_data(AdminOut.from_obj(admin))


@router.delete(
    "/{id:int}",
    response_model=AdminResponse,
    response_model_exclude_defaults=True,
)
async def remove_admin(
    id: AdminID,
    service: FromDishka[IAdminService],
) -> AdminResponse:
    admin = await service.remove(id)
    return APIResponse.from_data(AdminOut.from_obj(admin))
