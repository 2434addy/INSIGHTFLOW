"""
Base repository — common CRUD patterns for all data access classes.

Provides generic get-by-id, list-with-pagination, create, update, and
soft-delete operations. Concrete repositories inherit and add
domain-specific queries.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel, SoftDeleteMixin
from app.utils.pagination import decode_cursor, encode_cursor

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository with common data access patterns.

    Subclasses set `model` to their SQLAlchemy model class.
    """

    model: type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        """Fetch a single entity by primary key, respecting soft-delete."""
        query = select(self.model).where(self.model.id == entity_id)
        if issubclass(self.model, SoftDeleteMixin):
            query = query.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        *filters: Any,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[ModelT], str | None]:
        """
        Paginated list with cursor-based pagination.

        Returns (items, next_cursor). next_cursor is None if no more pages.
        """
        query = select(self.model)

        if issubclass(self.model, SoftDeleteMixin):
            query = query.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]

        for f in filters:
            query = query.where(f)

        if cursor:
            sort_value, last_id = decode_cursor(cursor)
            query = query.where(self.model.id > last_id)

        query = query.order_by(self.model.id).limit(limit + 1)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            last = items[-1]
            next_cursor = encode_cursor(str(last.created_at), last.id)

        return items, next_cursor

    async def create(self, entity: ModelT) -> ModelT:
        """Persist a new entity."""
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Flush changes to an existing entity."""
        await self.db.flush()
        return entity

    async def count(self, *filters: Any) -> int:
        """Count entities matching the given filters."""
        query = select(func.count(self.model.id))
        if issubclass(self.model, SoftDeleteMixin):
            query = query.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        for f in filters:
            query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar_one()
