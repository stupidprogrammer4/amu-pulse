"""Every model module must be imported here, or Alembic autogenerate will not
see its tables and will happily generate a migration that drops them."""

from src.models.base import Base

__all__ = ["Base"]
