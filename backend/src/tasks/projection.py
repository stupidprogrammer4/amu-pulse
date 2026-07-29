from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, get_args

from dishka.integrations.taskiq import FromDishka, inject
from pydantic import BaseModel

from src.common.bases.projection import (
    TBatchPayloadProjection,
    TBatchProjection,
    TESProjection,
    TPayloadProjection,
)
from src.tasks.broker import broker


def _dispatch_after(
    projection_cls: type[Any],
    method: str,
    task_prefix: str,
    id_attr: str | None,
    batch: bool = False,
) -> Callable[..., Callable[..., Any]]:
    name = projection_cls.__name__.lower()
    task_name = f"{task_prefix}_{name}"
    queue_name = f"{name}_queue"

    async def _task(id: Any, projection: Any) -> bool:
        result = await getattr(projection, method)(id)
        return result

    _task.__name__ = task_name
    _task.__qualname__ = task_name
    # resolve the concrete projection from dishka by its type
    _task.__annotations__ = {
        "id": list[int] if batch else int,
        "projection": FromDishka[projection_cls],
        "return": bool,
    }

    registered: Any = broker.task(task_name=task_name, queue_name=queue_name)(
        inject(_task, patch_module=True)
    )

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            if batch:
                ids = (
                    list(result)
                    if id_attr is None
                    else [getattr(item, id_attr) for item in result]
                )
                await registered.kiq(ids)
            else:
                await registered.kiq(getattr(result, id_attr or "id"))
            return result

        return wrapper

    return decorator


def project(
    projection_cls: type[TESProjection],
    id_attr: str = "id",
) -> Callable[..., Callable[..., Any]]:
    return _dispatch_after(projection_cls, "project", "run", id_attr)


def batch_project(
    projection_cls: type[TBatchProjection],
    id_attr: str | None = "id",
) -> Callable[..., Callable[..., Any]]:
    return _dispatch_after(
        projection_cls, "batch_project", "run_batch", id_attr, batch=True
    )


def unproject(
    projection_cls: type[TESProjection],
    id_attr: str = "id",
) -> Callable[..., Callable[..., Any]]:
    return _dispatch_after(projection_cls, "unproject", "unproject", id_attr)


def _payload_model(projection_cls: type[Any]) -> type[BaseModel]:
    model: type[BaseModel] | None = None
    for base in getattr(projection_cls, "__orig_bases__", []):
        for arg in get_args(base):
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                model = arg
                break
    if model is None:
        raise TypeError(
            f"{projection_cls.__name__} names no payload model to project"
        )
    return model


def _dispatch_payload_after(
    projection_cls: type[Any],
    method: str,
    task_prefix: str,
    batch: bool = False,
) -> Callable[..., Callable[..., Any]]:
    name = projection_cls.__name__.lower()
    task_name = f"{task_prefix}_{name}"
    queue_name = f"{name}_queue"
    model = _payload_model(projection_cls)

    async def _task(payload: Any, projection: Any) -> bool:
        rebuilt = (
            [model.model_validate(row) for row in payload]
            if batch
            else model.model_validate(payload)
        )
        result = await getattr(projection, method)(rebuilt)
        return result

    _task.__name__ = task_name
    _task.__qualname__ = task_name
    # dishka resolves the concrete projection off this annotation
    _task.__annotations__ = {
        "payload": list[dict[str, Any]] if batch else dict[str, Any],
        "projection": FromDishka[projection_cls],
        "return": bool,
    }

    registered: Any = broker.task(task_name=task_name, queue_name=queue_name)(
        inject(_task, patch_module=True)
    )

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            dumped = (
                [item.model_dump(mode="json") for item in result]
                if batch
                else result.model_dump(mode="json")
            )
            if dumped:
                await registered.kiq(dumped)
            return result

        return wrapper

    return decorator


def payload_project(
    projection_cls: type[TPayloadProjection],
) -> Callable[..., Callable[..., Any]]:
    return _dispatch_payload_after(projection_cls, "project", "payload")


def batch_payload_project(
    projection_cls: type[TBatchPayloadProjection],
) -> Callable[..., Callable[..., Any]]:
    return _dispatch_payload_after(
        projection_cls, "batch_project", "batch_payload", batch=True
    )
