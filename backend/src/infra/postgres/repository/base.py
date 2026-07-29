from typing import (
    Any,
    AsyncIterator,
    Generic,
    Optional,
    Sequence,
    TypeVar,
    get_args,
    get_origin,
)

from ..uow import PGUnitOfWork
from ..models.typing import (
    TModel,
    TIDModel,
    TTimestampModel,
    TIDTimestampModel,
)
from ..models.base import BaseModel
from src.common.bases.dtos import SupportsToRow
from src.common.bases.results import PagedType
from sqlalchemy import (
    Select,
    Values,
    column,
    func,
    inspect,
    literal,
    select,
    update,
    delete,
    insert,
    values,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import InstrumentedAttribute, Mapped
from sqlalchemy.sql.dml import ReturningInsert, ReturningUpdate
from sqlmodel import col


T = TypeVar("T", bound=BaseModel)


class PGReader:
    def __init__(self, uow: PGUnitOfWork):
        self.session = uow.session


class PGRepository(PGReader, Generic[TModel]):
    __model__: type[TModel]
    __model_name__: str

    _managed_columns = frozenset({"created_at", "updated_at"})

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base)
            args = get_args(base)

            if not origin or not args:
                continue

            if isinstance(args[0], TypeVar):
                continue

            if isinstance(origin, type) and issubclass(origin, PGRepository):
                model_cls = args[0]
                cls.__model__ = model_cls
                cls.__model_name__ = model_cls.__name__.removesuffix("Model")
                break

    async def create(self, data: TModel) -> TModel:
        stmt = (
            insert(self.__model__)
            .values(**data.to_row())
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def bulk_create(self, data: Sequence[TModel]) -> Sequence[TModel]:
        stmt = (
            insert(self.__model__)
            .values([d.to_row() for d in data])
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_stream(
        self, yield_per: int = 100
    ) -> AsyncIterator[TModel]:
        stmt = select(self.__model__).execution_options(yield_per=yield_per)
        stream = await self.session.stream_scalars(stmt)
        async for row in stream:
            yield row

    async def get_all(self) -> Sequence[TModel]:
        stmt = select(self.__model__)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _paginate(
        self, stmt: Select[Any], offset: int, limit: int
    ) -> PagedType[TModel]:
        total = func.count().over().label("total")
        paged = stmt.add_columns(total).offset(offset).limit(limit)
        result = await self.session.execute(paged)
        rows = result.unique().all()
        items = [row[0] for row in rows]
        total_items = rows[0][-1] if rows else 0
        return PagedType(items=items, total_items=total_items)

    def _values_grid(self, data: Sequence[SupportsToRow]) -> Values:
        mapper = inspect(self.__model__)
        rows = [row.to_row(exclude_unset=True) for row in data]
        names = list(rows[0].keys())
        types = {name: mapper.columns[name].type for name in names}
        return values(
            *(column(name, types[name]) for name in names),
            name="bulk_values",
        ).data(
            [
                tuple(literal(row[name], types[name]) for name in names)
                for row in rows
            ]
        )

    def _upsert_stmt(
        self,
        data: SupportsToRow | Sequence[SupportsToRow],
        index_elements: Sequence[Mapped[Any]],
    ) -> ReturningInsert[tuple[TModel]]:
        conflict_keys = {
            self._column_key(element) for element in index_elements
        }
        rows = (
            [data.to_row()]
            if isinstance(data, SupportsToRow)
            else [row.to_row() for row in data]
        )
        base = pg_insert(self.__model__).values(rows)
        set_keys = [name for name in rows[0] if name not in conflict_keys]
        set_: dict[str, Any] = {name: base.excluded[name] for name in set_keys}
        stmt = base.on_conflict_do_update(
            index_elements=list(index_elements), set_=set_
        ).returning(self.__model__)
        return stmt

    def _bulk_update_stmt(
        self,
        data: Sequence[SupportsToRow],
        key: Mapped[Any],
    ) -> ReturningUpdate[tuple[TModel]]:
        grid = self._values_grid(data)
        key_name = self._column_key(key)
        skip = self._managed_columns | {key_name}
        set_keys = [name for name in grid.c.keys() if name not in skip]
        stmt = (
            update(self.__model__)
            .where(key == grid.c[key_name])
            .values({name: grid.c[name] for name in set_keys})
            .returning(self.__model__)
        )
        return stmt

    @staticmethod
    def _column_key(element: Mapped[BaseModel]) -> str:
        return element.key  # type: ignore


class PGIDRepository(PGRepository[TIDModel]):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)

    async def get_by_id(self, id: int) -> Optional[TIDModel]:
        stmt = select(self.__model__).where(col(self.__model__.id) == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_id(self, id: int) -> Optional[TIDModel]:
        stmt = (
            delete(self.__model__)
            .where(col(self.__model__.id) == id)
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_row_by_id(
        self, id: int, data: TIDModel
    ) -> Optional[TIDModel]:
        row = await self.update_by_id(id, data.to_row())
        return row

    async def update_by_id(
        self, id: int, row: dict[str, Any]
    ) -> Optional[TIDModel]:
        stmt = (
            update(self.__model__)
            .where(col(self.__model__.id) == id)
            .values(**row)
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[int]) -> Sequence[TIDModel]:
        stmt = select(self.__model__).where(col(self.__model__.id).in_(ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_by_ids(
        self, ids: Sequence[int], row: dict[str, Any]
    ) -> Sequence[TIDModel]:
        stmt = (
            update(self.__model__)
            .where(col(self.__model__.id).in_(ids))
            .values(**row)
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_ids(self, ids: Sequence[int]) -> Sequence[TIDModel]:
        stmt = (
            delete(self.__model__)
            .where(col(self.__model__.id).in_(ids))
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert_by_id(self, id: int, row: dict[str, Any]) -> TIDModel:
        stmt = (
            pg_insert(self.__model__)
            .values(id=id, **row)
            .on_conflict_do_update(
                index_elements=[col(self.__model__.id)], set_=row
            )
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


class PGTimestampRepository(PGRepository[TTimestampModel]):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)

    async def get_stream_by_date_range(
        self, start: str, end: str, yield_per: int = 100
    ) -> AsyncIterator[TTimestampModel]:
        stmt = (
            select(self.__model__)
            .where(
                col(self.__model__.created_at) >= start,
                col(self.__model__.created_at) <= end,
            )
            .execution_options(yield_per=yield_per)
        )
        stream = await self.session.stream_scalars(stmt)
        async for row in stream:
            yield row

    async def delete_by_date_range(
        self, start: str, end: str
    ) -> Sequence[TTimestampModel]:
        stmt = (
            delete(self.__model__)
            .where(
                col(self.__model__.created_at) >= start,
                col(self.__model__.created_at) <= end,
            )
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_by_date_range(
        self, start: str, end: str, data: BaseModel
    ) -> Sequence[TTimestampModel]:
        stmt = (
            update(self.__model__)
            .where(
                col(self.__model__.created_at) >= start,
                col(self.__model__.created_at) <= end,
            )
            .values(**data.to_row())
            .returning(self.__model__)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PGTimestampIDRepository(
    PGIDRepository[TIDTimestampModel], PGTimestampRepository[TIDTimestampModel]
):
    def __init__(self, uow: PGUnitOfWork):
        super().__init__(uow)
