from __future__ import annotations

from typing import Awaitable, Callable

import typer

app = typer.Typer(help="one-off operational scripts", no_args_is_help=True)


@app.callback()
def _main() -> None: ...


def _run(fn: Callable[..., Awaitable[None]]) -> None:
    import asyncio

    import src.tasks.broker  # noqa: F401 — boots the modules
    from src.core.config import get_settings
    from src.infra.postgres.connection import PGConnection
    from src.infra.postgres.uow import PGUnitOfWork

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
                await fn(uow, settings)
        finally:
            await pg.dispose()

    asyncio.run(main())


@app.command("create-super-admin")
def create_super_admin_command(
    username: str = typer.Option(..., "--username", "-u"),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
    ),
) -> None:

    async def run(uow, settings) -> None:
        from scripts.super_admin import create_super_admin

        admin, created = await create_super_admin(
            uow, settings, username, password
        )
        if created:
            typer.secho(
                f"✓ created super admin '{admin.username}'",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho(
                f"admin '{admin.username}' already exists, left as it is",
                fg=typer.colors.YELLOW,
            )

    _run(run)
