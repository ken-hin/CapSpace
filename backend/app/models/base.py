"""Declarative base and shared model mixins.

Defines the single :class:`Base` that all ORM models inherit from (so they
share one ``MetaData`` / mapper registry) and reusable column mixins such as
:class:`TimestampMixin`.
"""

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class shared by all SQLAlchemy models.

    Every model in the application inherits from this class so they all
    register on the same metadata, which Alembic and ``create_all`` use to
    emit DDL.
    """
    pass


class TimestampMixin:
    """Mixin adding database-managed ``created_at`` / ``updated_at`` columns.

    Both timestamps default to the server's current time on insert;
    ``updated_at`` is additionally refreshed on every update. Mix into any model
    that needs audit timestamps.

    Attributes:
        created_at: Row creation time (set once, server-side).
        updated_at: Last modification time (refreshed server-side on update).
    """
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
