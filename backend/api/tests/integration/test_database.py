
import pytest

from src.infra.postgres.uow import PGUnitOfWork


@pytest.mark.usefixtures("migrated_test_db")
async def test_database_is_migrated_and_reachable(uow: PGUnitOfWork) -> None:
    now = await uow.now()
    assert now is not None
