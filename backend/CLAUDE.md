# Goldis backend — architecture & conventions

A FastAPI + SQLModel/Postgres + Elasticsearch + taskiq + dishka **modular monolith**.
All imports are absolute from `src...` (never `backend.src...`).

## Graphify usage (important)

- Before reading files to understand project structure, query the graphify graph first.
- Use these instead of grep or reading files across the whole project to find
  relationships, dependencies, and patterns in similar modules:
  - `graphify query "<natural-language question>"` — a subgraph relevant to a question
  - `graphify path "A" "B"` — the path between two concepts
  - `graphify explain "<node>"` — all connections of a node with confidence tags
- Only read raw files when the graph doesn't give a sufficient answer or when you
  need to see the exact implementation.
- Before implementing a new module, first use graphify to see how similar modules
  are built, and follow the same pattern and structure.

## Working agreement (definition of done)
Before any task is considered finished:
1. **Tests are written** — BOTH `tests/unit` (unit) and `tests/integration` (integration).
2. **All tests pass** (`pytest`). Only after green is it OK to commit.
3. **Zero type errors** — `pyright` reports no errors anywhere in the project.
4. **Clean lint/format** — `ruff format src tests` leaves nothing to change and
   `ruff check src tests` is clean (79-column limit included).

Prefer proper typed solutions over `cast` / `# type: ignore`.

## Code style
- **Single return per function.** Prefer one exit point: seed a `result` variable
  with the default and reassign it in branches, instead of returning from inside
  `if`/branches. Do **not** use multiple `return` statements to pick a value.
  ```python
  # do this
  result = b
  if something:
      result = a
  return result

  # not this
  if something:
      return a
  return b
  ```
  Bind the value to a variable first — **never `return func()` / `return await func()`
  directly**, even for a one-line service passthrough (`m = await self.repo.x()` then
  `return m`).
- **Max line length is 79 columns — everywhere** (code, docstrings, comments,
  tests). Enforced by `ruff` (`line-length = 79` in `pyproject.toml`); a wide line
  is an error, not a preference. Break a long boolean guard across lines in
  parentheses (`if (\n    a\n    and b\n):`) rather than one wide line, and don't
  pack multiple steps onto one line to save space. Readable beats dense. The only
  escape hatch is a literal that genuinely cannot be split (an API URL) — that one
  gets `# noqa: E501`.
- **More than one argument ⇒ one argument per line.** A `def` taking more than a
  single real parameter (`self`/`cls` don't count) puts every parameter on its own
  line, with a trailing comma after the last one (the trailing comma is what keeps
  the formatter from re-joining them):
  ```python
  async def reprice(
      self,
      platform_id: int,
      metal_id: int,
  ) -> BatchResultType:
  ```
  Run `ruff format` after editing; it honours the trailing comma.
- **Comment sparingly — one short line, or nothing.** A comment is AT MOST one
  short line, and only on a non-obvious *why*. Never write a multi-line
  explanatory comment block, never annotate the obvious, never restate the code —
  let names and the (required) function docstrings carry the meaning. Pragmas
  (`# noqa`, `# type: ignore`, `# pyright:`) are exempt.
- **Minimize IO — never re-query what you already have.** Fetch each thing from the DB
  exactly once. `create` / `update_by_id` / `update_row_by_id` / `bulk_create` all
  `RETURNING` the row(s) — use that returned value; do **not** `get_by_id` again after a
  write, and don't re-read a parent to load children you just created (attach them:
  `order.items = list(items)`). No redundant ownership/pre-fetch reads before an action
  whose own query already validates + returns (e.g. `mark_paid` returns the row — don't
  `get_owned` first just to read its id). The request unit-of-work commits on success and
  rolls back on any exception, so a guard that raises after a write still undoes it.
- **Scope each fetch to what the caller uses — no one-size-fits-all fetcher.** Don't
  route every call site through a single broad helper that fetches the union and lets each
  caller pick out its slice. When callers need different slices, give each its own
  logic + query scoped to exactly the data it consumes: a caller that knows a single
  `(platform, metal)` fetches that one row (`get_selling_margin`), not the whole margin
  set filtered down afterward; a caller spanning a set fetches the set (`get_selling_margins`).
  The query's shape (single-key vs. batched) must mirror what the caller actually reads —
  over-fetching then discarding is the same waste as re-querying. Two similar-looking paths
  are two helpers, not one generic one with a filter tacked on.
- **No UPPERCASE module-level globals.** Don't define ad-hoc config/magic values
  (`WINDOW_MINUTES`, `BATCH_SIZE`, `TOP_K`, task-name strings, …) as UPPER_CASE module
  constants. Scope each value to the class/function that uses it — a lowercase class
  attribute (`window_minutes = 14`), a local, or an inline literal. (Exceptions: the
  per-module `config/resources.py` message-code registries, `config/constants.py`
  values, and seeder declarative data tables.)
- **All imports at the top of the file — never inside a function.** The broker-first
  invariant (see Tasks) already makes top-level imports of `tasks/`/broker safe.
- **Services never import from `routers/`.** When an HTTP action must dispatch a
  background task, the **router** kicks it after the service returns (routers → tasks).
  A service may only kick its own module's tasks when the dispatch is part of a
  cross-module `I*Service` contract (e.g. `IMessageService.send_sms`) — imported at
  the top, aliased `task: Any = <task>` (the `@inject` wrapper rewrites signatures).
- **Boundary outputs are own-domain types.** Anything a service returns to a consumer
  outside its module (another module via `I*Service`, a router, a task) must be the
  module's **own** domain model / `*Out` schema / domain dataclass — wrappers like
  `Sequence`/`PagedType`/`BatchResultType` are fine, but the payload type inside them
  belongs to the module. Never re-export another module's model/dataclass as your
  output; map it into your own type (see `AdminOtpIssueType`, `SalesTrendOut`).
- **Bind an `await` before using it.** Never `return await f()`, `if await f():`,
  `while await f():`, or `for x in await f():` (incl. inside comprehensions) — call,
  assign to a named variable, then branch/loop/return on the variable. Same for
  `async for x in await f():` (bind the stream first). It keeps every intermediate
  value inspectable when debugging.
- **`app/helpers.py` holds classes only — no raw module-level functions.** Group the
  helper logic into a purposeful class (`DiscountRules`, `PaymentSplitter`,
  `CartLineBuilder`) the service instantiates in `__init__`; constants scope as class
  attributes.
- **Private `_helper` methods must earn their keep (DRY).** A protected method used
  once gets inlined into its caller; only extract when at least two call sites share it.
- **Patches are model writes, not raw dicts.** Build a partially-populated model
  (`Model(field=…)` or `Model(**dto.to_row())`) and pass it to `update_row_by_id` —
  never hand-build `{"col": value}` dicts for updates.
- **State machines are one class in `app/helpers.py`** (e.g. `VerificationStateMachine`):
  a transition table + guard/transition methods returning patch models. Not a pile of
  module functions, not `_protected` methods on the service.
- **Gateway results follow the `SourceQuote` pattern** (`metals/domain/quotes.py`): a
  frozen dataclass in its own domain file (`quotes.py`, `identity.py`, `deliveries.py`)
  carrying the real payload (names, prices, …) plus `error: <X>ErrorInfo | None` (a
  TypedDict: kind/exc_type/message/status_code) and a `.failed(error)` classmethod.
  Gateways NEVER raise — the contract always holds; services read `result.error`,
  no try/except around gateway calls.
- **Docstrings are for functions — and ONLY for functions.** No module docstrings,
  no class docstrings. Every `def` / `async def` — service, repository, router
  handler, task, helper, gateway, `I*Service` Protocol method, `__init__` — carries
  exactly one docstring, in exactly this shape:
  ```python
  async def get_by_id(self, id: int) -> Optional[TIDModel]:
      """
      Desc: Get a record by ID.
      Args:
          id (int): ID of the record to retrieve.
      Returns:
          return (Optional[TIDModel]): Found record or None.
      """
  ```
  - `Desc:` is exactly **one** line — if it doesn't fit on one line, the sentence is
    too long, not the docstring too small.
  - Every parameter is listed as `name (Type): what it is`; `self`/`cls` never are.
  - The return entry is literally `return (Type): …`.
  - Drop the whole `Args:` block when there are no parameters; drop the whole
    `Returns:` block when the function returns `None`.
  - Types mirror the real annotation. No other sections (no `Raises:`, no prose
    paragraphs, no examples).
  - Exception: in `tests/`, `test_*` functions and fixtures take **no** docstring —
    the test name is the description. Shared test helpers/factories follow the
    format above.

## Money
All monetary amounts are integer **Rial** everywhere — stored, computed, and passed
around as Rial (`RialType` = BIGINT). Toman is display-only (1 Toman = 10 Rial); render
with `persian_utils.format_rial` / `format_toman`. Never store Toman or floats for money.

## Top-level layout (`backend/src`)
- `common/` — shared bases: `errors/` (APPException + `...Exception` + `...ErrorOut`),
  `bases/` (schemas: BaseOutput/PagerMeta/…, results: BatchResultType, services:
  BaseService, projection: AbstractESProjection), plus `constants`, `enums`, `types`, `utils`.
- `core/` — `config` (pydantic Settings from `config.yml`), `provider` (dishka CoreProvider),
  `bootstrap` (module auto-discovery), `logger`, `resources` (message codes).
- `infra/` — outward adapters: `postgres/` (orm, repository, connection, uow),
  `es/` (client, repository), `redis/` (client), `excel/` (row, reader, writer).
- `tasks/` — `broker` (taskiq) and the `project` decorator.
- `web/` — app, response, error_handlers, middlewares.
- `modules/<group>/<name>/` — feature modules, grouped by domain (scaffold with the CLI below).

## Module groups
Modules live one level under a **domain group** — the group is a pure namespace
(no shared code inside a group folder; cross-module calls always go through an
injected `I*Service` Protocol, same-group or not):
- `catalog/` — products, categories, attributes, brands
- `market/` — metals, fees, taxes (pricing lands here next)
- `channels/` — platforms (+ per-metal margins), marketplaces (seller config),
  websites (API keys + dynamic param/settings, EAV-style)
- `ops/` — storage, system, jobs
Planned groups from the merge plan (docs/talamala-v4-merge.md): `identity/`,
`commerce/` (carts, orders, payments, discounts), `finance/` (wallet, treasury,
intercompany), `logistics/` (inventory, fulfillment).
Keep it one level deep: `modules/<group>/<name>/…` — never nest further.

## Module CLI
Scaffold modules with the manager CLI (run from `backend/`), passing `<group>.<name>`:
```bash
python -m src.manager module catalog.<name>           # CRUD (Postgres only)
python -m src.manager module catalog.<name> --cqrs    # + ES read-model + projection + app/commands.py + app/queries.py
python -m src.manager module catalog.<name> --http    # + infra/gateways.py
python -m src.manager module catalog.<name> --excel   # + infra/exporters.py
python -m src.manager module catalog.<name> --tasks   # + tasks/ (taskiq background tasks)
```

## Module structure
```
modules/<group>/<name>/
├── domain/           # models.py (SQLModel), documents.py (ES), dtos.py, schemas.py, enums.py
├── app/              # services.py, helpers.py, commands.py/queries.py (CQRS)
├── infra/            # repository.py, projections.py, gateways.py, exporters.py
├── routers/          # one router per concern file (admin.py, account.py, …); __init__.py stays EMPTY
├── tasks/            # taskiq tasks in named files (reprice.py, send.py, …); __init__.py stays EMPTY
├── config/           # the module's small declarations, grouped out of the root:
│                     #   constants.py (values + IDEncryption), dependencies.py
│                     #   (FastAPI deps), resources.py (message codes); __init__.py EMPTY
├── interfaces.py     # I*Service Protocol contracts
└── providers.py      # dishka provider
```
- `constants.py` / `dependencies.py` / `resources.py` live under `config/`, not the
  module root — import them from there (`...<name>.config.resources`,
  `...<name>.config.constants`, `...<name>.config.dependencies`). Only modules that
  need a given file have it.
- `bootstrap` discovers modules under the group folders (a package counts as a
  module when it has a `domain`/`app` layer) and scans: `domain.models`,
  `domain.documents`, `providers`, and every FILE inside `routers/` and `tasks/`
  (`import_package_modules`) — no aggregator imports needed; a router/task
  registers by existing in its file. Module `__init__.py` files hold nothing.
- **CRUD** = Postgres only. **CQRS** = Postgres write side + ES read-model kept in
  sync by a projection.
- Dependencies point inward: `routers`/`tasks`/`app`/`infra` → `domain`; `domain` knows
  nothing about DB/ES/HTTP.

## Services
- A module's service inherits `BaseIDService[<Model>]` (or `BaseService[<Model>]` for
  non-id models) from `common/bases/services`. The generic arg binds `__model__` /
  `__model_name__` (via `__init_subclass__`) and provides the guard helpers
  `_check_for_id_existence`, `_check_batch_data`, `_check_not_empty_dict/list`,
  `_check_for_existence` (which raise `NotFoundException` / `ValidationException`).
- The service must structurally satisfy its `I<Name>Service` Protocol (in `app/interfaces.py`);
  the provider binds it with `provide(Service, provides=IService)`.
- **A `*Query` class reads from a non-DB source — Elasticsearch or an external system —
  never Postgres.** The "query" name is reserved for the read side that goes somewhere
  other than the database (e.g. `ListingSearchQuery` over ES). Anything that reads
  Postgres is a **service** (or a method on one), not a query. Don't build a
  `SomethingQuery` that fans out over PG repos; put that read logic in the relevant
  service and compose from existing `I*Service`s.

## Postgres / ORM
- `infra/postgres/models/` and `infra/postgres/repository/` are **packages**, each
  split into `base.py` (the classes) + `typing.py` (the `TypeVar`s). **Every
  `__init__.py` in the project is EMPTY** — import from the concrete file
  (`from src.infra.postgres.models.base import BaseModel`,
  `from src.infra.postgres.models.typing import TModel`), never a package root.
- Models inherit from `src.infra.postgres.models.base`: `BaseModel` →
  `BaseIDModel` / `BaseTimestampModel` / `BaseIDTimestampModel`.
- `BaseModel` is `AsyncAttrs, SQLModel` with:
  - `to_row(exclude_unset=True)` — column dict for SQL writes (Schema-in).
  - auto `__tablename__` = `tbl_` + pluralised class name minus `Model`, lowercased
    (`ProductModel` → `tbl_products`, `CategoryModel` → `tbl_categories`). Pluralisation
    uses `common/utils/string_utils.pluralize` (simple English heuristics); override
    `__tablename__` for irregular nouns.
- Integers are **BIGINT** (`sa_type=BigInteger`); PK is `id: int | None` autoincrement.
- Timestamps (`created_at`/`updated_at` via `TimestampField`) are `DateTime(timezone=True)`,
  filled by the DB on INSERT via `server_default NOW()` (tz-aware UTC) and returned through
  RETURNING — not set python-side. `date_utils.utc_now()` is tz-aware UTC.
- Two complementary "types" modules:
  - `src.infra.postgres.types` — **column/Field factories** that build the SQLAlchemy
    column: `IDField`, `IntField`/`SmallIntField`/`BigIntField`, `BoolField`,
    `FloatField`/`NumericField`, `CharField(len)`, `TextField`, `DateField`,
    `TimestampField`, `JSONBField`, `EnumField(EnumCls)`, `ForeignKeyField(target)`.
    All take `**kwargs: Unpack[ColumnKwargs]` (the `Column` kwargs as a `TypedDict`);
    columns are **NOT NULL by default** — pass `nullable=True` to opt out.
  - `src.common.types` — **pydantic validation aliases** (value constraints):
    `BigIntType`, `RialType`, `StrType`(35), `LStrType`(100), `SlugType`(55),
    `ContentType`, `RateType`, `IdType`, …
  - Combine them on a column: `name: StrType = CharField(35)`.
- Repositories subclass `PG[ID|Timestamp|TimestampID]Repository`; build query predicates
  with `col(Model.field)`.

## Write path (DTOs & repo writes)
- **Input DTOs = `BaseDTO`** (`common/bases/dtos.py`) — pure **pydantic**, NOT SQLModel.
  Has `to_row(exclude_unset=True)`. Keeps `domain` decoupled from `infra.postgres`
  without dragging SQLAlchemy into `common`. Every module's Create/Update DTO inherits it.
- **Repo writes take a model or a dict, never a DTO.** Two update modes on `PGIDRepository`:
  - `update_row_by_id(id, data: TIDModel)` — model in; only set fields are written
    (`to_row` drops unset → acts as a patch). Pass a partially-populated model
    (e.g. `CategoryModel(parent_id=…)`) instead of a row-mirror DTO.
  - `update_by_id(id, row: dict)` — plain dict in. `update_by_ids` / `upsert_by_id`
    and module-level update methods also take `dict`.
- **The service holds the validated `BaseDTO`**, runs `_check_not_empty_dict(data.to_row())`
  (the empty-patch guard lives in the service, not the repo), then passes a `dict` for
  patches or a model for full-row updates.
- **`SupportsToRow` protocol** (`common/bases/dtos.py`) is what `_values_grid` /
  `_upsert_stmt` / `_bulk_update_stmt` accept, so both model instances and DTOs satisfy it.
- `_values_grid` (bulk updates) uses `to_row(exclude_unset=True)`: pass full models, only
  set fields are written. Contract — every row in a batch must set the same fields.
- **Repositories hold single-statement queries only.** One `stmt` per method, run via
  `self.session.execute(stmt)` — never `session.add`/`add_all` loops, never a repo method
  that strings several statements together as "logic", and **zero business logic** (no
  branching on domain rules, no computing values — just build and run the query).
- **Repo method names describe the query, not the caller.** Name by what the statement
  selects/filters/writes (`get_by_order_id`, `count_unpaid`, `expire_by_order_ids`,
  `stream_expired_ids`) — never mirror the service method that happens to call it
  (a service `renew_window` does not get a repo `renew_window`). The business verb lives
  in the service; the repo name is about rows and predicates.
- Batch **replace-set** writes are
  always TWO repo methods, orchestrated by the service:
  1. `remove_missing(owner_id, keep)` — `delete(...).where(owner match, key.not_in(keep))`
  2. `bulk_upsert(items)` — `pg_insert(Model).values([item.to_row() for item in items])`
     with `on_conflict_do_nothing()` for pure link rows, or
     `on_conflict_do_update(index_elements=[...], set_={...: stmt.excluded...})` when the
     row carries a payload column.
  The replace logic (validate → `remove_missing` → `bulk_upsert`) lives in the **service**
  (reference: `WebsiteBrandRepository`, `PermissionRepository`).

## Errors
- Abstract base `APPException` (`common/errors/base.py`); concrete classes are named
  `...Exception` (ValidationException, NotFoundException, UnAuthorizedException,
  ForbiddenException, ConflictException) and serialize via `as_schema()` → `...ErrorOut`.

## Types
- `@dataclass(frozen=True, slots=True)` for internal named return values (e.g.
  `BatchResultType` in `common/bases/results.py`).
- **Never return a bare multi-field tuple** from a service / repository method (e.g.
  `-> tuple[int, Decimal]`). Give the shape a name — a frozen dataclass in the owning
  module's `domain/` (next to `quotes.py`) — so callers read `x.selling_per_gram`, not
  `x[0]`. A single-column projection (`-> int | None`) or the id-plus-value pair rows of a
  batch map (`Sequence[tuple[int, int]]` folded straight into a `dict`) stay tuples.
- `TypedDict` for dict/wire shapes; `pydantic`/`SQLModel` for validation & ORM.

## Elasticsearch (CQRS)
- Documents = `elasticsearch.dsl.AsyncDocument` subclasses (read models) in
  `domain/documents.py`.
- `ESClient` wraps `AsyncElasticsearch`; `ESRepository[TDoc]` gives CRUD + `search()`
  (+ `bulk_insert`), passing `using=` explicitly.
- Projections subclass `AbstractESProjection[TPGRepository, TESRepository]` and implement
  `project(id)` (read PG → write ES).
- Decorate write service methods with `@project(SomeProjection)` (`src/tasks/projection.py`):
  after the method returns a model with `.id`, a taskiq job reprojects it into ES.

## Redis
- `RedisClient` (`infra/redis/client.py`) wraps `redis.asyncio.Redis`; use `.client`.

## Excel
- `ExcelRow` base + the `Row(title=...)` field helper (`infra/excel/row.py`).
- `ExcelWriter` / `ExcelReader` are async over a `ProcessPoolExecutor` (separate worker
  process). Worker job functions must be module-level or `@staticmethod` (picklable) —
  never bound methods (the pool isn't picklable).

## DI (dishka)
- `CoreProvider` provides `Settings`, `PGConnection` + request-scoped `PGUnitOfWork`,
  `RedisClient`, `ESClient`.
- Module `app/providers.py`: `scope = Scope.REQUEST`; `provide(Repository)` and
  `provide(Service, provides=IService)` (bind impl to its Protocol).

## Tasks (taskiq)
- Broker in `src/tasks/broker.py` — the broker instance is defined **before**
  `boot_providers()` so `@project`/task imports don't cause an import cycle.
- Every entrypoint that imports module code (web/app.py, a seeder using the
  create commands) must `import src.tasks.broker` **first**: broker.py runs its
  own module boot, and letting a module import trigger it mid-boot re-enters
  half-imported modules (circular import / missing providers).
- Module background tasks live in the module's `tasks/` package (imported by
  `bootstrap.boot_tasks`); modules without tasks simply have no `tasks/` folder.

## Config
- `config.yml` (sample: `config.yml.sample`). `PostgreSQLConfig` uses `pool_size` /
  `max_overflow`. Postgres has two DSNs: `dsn` (dev) and `test_dsn` (tests).

## Migrations (alembic)
- `migrations/env.py` loads every model via `get_bootstrapper().boot_sqlmodels()` and
  uses `target_metadata = SQLModel.metadata`, so autogenerate sees the whole schema.
- The DB URL comes from `config.yml` (`get_settings().postgresql.dsn`) unless one is set
  programmatically (the test suite injects `test_dsn`) — don't hardcode it in `alembic.ini`.
- Autogenerate a revision: `alembic revision --autogenerate -m "..."`; apply: `alembic upgrade head`.

## Tests
- `tests/unit/` — fast, isolated, no external services (marker `unit`).
- `tests/integration/` — real database / live ASGI app (marker `integration`).
- **Tests are async** (`asyncio_mode = auto`); write `async def` tests.
- Markers are auto-applied by path (`tests/conftest.py`): fast tests with
  `pytest -m "not integration"`, full suite with `pytest`.
- **Integration tests always use `test_dsn`**, never the dev DB: depend on the
  `migrated_test_db` fixture (resets the schema + runs `alembic upgrade head` on `test_dsn`)
  and reach the DB via `pg` / `uow` (both bound to `test_dsn`).
- Shared fixtures live in `tests/conftest.py` (`pg`, `uow`, `clean_db`, `migrated_test_db`,
  `dishka_container`/`dishka_request`); providers/models are discovered via the bootstrapper,
  so new modules are picked up automatically.
- Every feature ships with both unit and integration tests before it's done (see the
  definition of done above).