from datetime import datetime
from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict

from getgather.database.connection import execute_insert, execute_query, fetch_one


class DBModel(BaseModel):
    """Base model for database records with common operations."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    created_at: datetime | None = None

    table_name: ClassVar[str]

    @classmethod
    def get(cls, id: int) -> Self | None:
        """Get a record by its ID."""
        query = f"SELECT * FROM {cls.table_name} WHERE id = ?"
        if row := fetch_one(query, (id,)):
            return cls.model_validate(row)
        return None

    @classmethod
    def add(cls, data: BaseModel) -> int:
        """Insert a new record and return its ID."""
        # Filter out None values and id field
        fields = {k: v for k, v in data.model_dump().items() if v is not None and k != "id"}

        placeholders = ", ".join("?" * len(fields))
        columns = ", ".join(fields.keys())

        query = f"""
            INSERT INTO {cls.table_name} ({columns})
            VALUES ({placeholders})
        """

        # Convert datetime objects to ISO format strings
        params = tuple(v.isoformat() if isinstance(v, datetime) else v for v in fields.values())
        cls.id = execute_insert(query, params)
        return cls.id

    @classmethod
    def update(cls, id: int, data: dict[str, Any]) -> None:
        """Update a record by its ID with the provided data."""
        # Filter out None values
        updates = {k: v for k, v in data.items() if v is not None}
        if not updates:
            return

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        query = f"""
            UPDATE {cls.table_name}
            SET {set_clause}
            WHERE id = ?
        """

        # Convert datetime objects to ISO format strings
        params = tuple(
            v.isoformat() if isinstance(v, datetime) else v for v in updates.values()
        ) + (id,)

        execute_query(query, params)
