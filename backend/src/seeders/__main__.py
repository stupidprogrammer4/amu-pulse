# isort: skip_file
# the broker boots the modules; importing it after them re-enters a
# half-imported package, so it has to come first (see CLAUDE.md, Tasks)
import asyncio

import src.tasks.broker  # noqa: F401

from src.core.config import get_settings
from src.infra.postgres.connection import PGConnection
from src.infra.postgres.uow import PGUnitOfWork
from src.seeders.assets import seed_assets
from src.seeders.sources import seed_sources


async def seed_all(uow: PGUnitOfWork) -> None:
    """
    Desc: Run every seeder in dependency order on one unit of work.
    Args:
        uow (PGUnitOfWork): Unit of work the seeders write through.
    """
    print(f"seeded {len(await seed_assets(uow))} assets")
    print(f"seeded {len(await seed_sources(uow))} sources")


async def main() -> None:
    """
    Desc: Open a Postgres connection and run every seeder through it.
    """
    settings = get_settings()
    pg = PGConnection(
        dsn=settings.postgresql.dsn,
        pool_size=settings.postgresql.pool_size,
        max_overflow=settings.postgresql.max_overflow,
        pool_timeout=settings.postgresql.pool_timeout,
        pool_recycle=settings.postgresql.pool_recycle,
    )
    try:
        async with PGUnitOfWork(pg) as uow:
            await seed_all(uow)
    finally:
        await pg.dispose()


if __name__ == "__main__":
    asyncio.run(main())
