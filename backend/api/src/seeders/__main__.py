# isort: skip_file
# the broker boots the modules, so it has to be imported first
import asyncio

import src.tasks.broker  # noqa: F401

from src.core.config import get_settings
from src.infra.postgres.connection import PGConnection
from src.infra.postgres.uow import PGUnitOfWork
from src.seeders.assets import seed_assets
from src.seeders.bubbles import seed_bubbles
from src.seeders.sources import seed_sources
from src.seeders.symbols import seed_symbols


async def seed_all(uow: PGUnitOfWork) -> None:
    print(f"seeded {len(await seed_assets(uow))} assets")
    print(f"seeded {len(await seed_sources(uow))} sources")
    # after assets: a symbol points at the asset it prices
    print(f"seeded {len(await seed_symbols(uow))} symbols")
    print(f"seeded {len(await seed_bubbles(uow))} bubbles")


async def main() -> None:
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
