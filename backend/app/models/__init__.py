"""SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Metadata for tables owned by this process."""
