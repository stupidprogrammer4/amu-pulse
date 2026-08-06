from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query

from src.modules.identity.auth.config.dependencies import admin_required
from src.modules.ops.logs.domain.dtos import LogSearch
from src.modules.ops.logs.domain.schemas import LogMeta, LogOut
from src.modules.ops.logs.interfaces import ILogService
from src.web.response import APIResponse

router = APIRouter(
    prefix="/panel/logs",
    tags=["Panel Logs"],
    route_class=DishkaRoute,
    dependencies=[admin_required],
)

PagedLogResponse = APIResponse[LogOut, LogMeta]
LogResponse = APIResponse[LogOut, None]


@router.get(
    "",
    response_model=PagedLogResponse,
    response_model_exclude_defaults=True,
)
async def search_logs(
    data: Annotated[LogSearch, Query()],
    service: FromDishka[ILogService],
) -> PagedLogResponse:
    result = await service.search(data)
    return APIResponse(success=True, data=result.data, meta=result.meta)


@router.get(
    "/traces/{request_id}",
    response_model=LogResponse,
    response_model_exclude_defaults=True,
)
async def get_log_trace(
    request_id: str,
    service: FromDishka[ILogService],
) -> LogResponse:
    lines = await service.get_by_request_id(request_id)
    return APIResponse.from_data(lines)
