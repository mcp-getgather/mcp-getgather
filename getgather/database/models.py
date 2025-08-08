import json
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict

from getgather.database.connection import execute_insert, execute_query, fetch_one


class DBModel(BaseModel):
    """Base model for database records with common operations."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    created_at: datetime | None = None

    @property
    def table_name(self) -> str:
        """Table name for this model. Should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement table_name property")

    def get(self, id: int) -> Self | None:
        """Get a record by its ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        if row := fetch_one(query, (id,)):
            return self.model_validate(row)
        return None

    def add(self) -> int:
        """Insert a new record and return its ID."""
        # Filter out None values and id field
        fields = {k: v for k, v in self.model_dump().items() if v is not None and k != "id"}

        placeholders = ", ".join("?" * len(fields))
        columns = ", ".join(fields.keys())

        query = f"""
            INSERT INTO {self.table_name} ({columns})
            VALUES ({placeholders})
        """

        # Convert datetime objects to ISO format strings
        params = tuple(v.isoformat() if isinstance(v, datetime) else v for v in fields.values())

        self.id = execute_insert(query, params)
        return self.id

    def update(self, id: int, data: dict[str, Any]) -> None:
        """Update a record by its ID with the provided data."""
        # Filter out None values
        updates = {k: v for k, v in data.items() if v is not None}
        if not updates:
            return

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            WHERE id = ?
        """

        # Convert datetime objects to ISO format strings
        params = tuple(
            v.isoformat() if isinstance(v, datetime) else v for v in updates.values()
        ) + (id,)

        execute_query(query, params)


class RRWebRecording(DBModel):
    """rrweb recording model for storing browser automation replays."""
    
    activity_id: int
    events_json: str
    event_count: int
    start_timestamp: int
    end_timestamp: int
    
    @property
    def table_name(self) -> str:
        return "rrweb_recordings"
    
    @property
    def events(self) -> list[dict[str, Any]]:
        """Parse and return the events as a Python list."""
        return json.loads(self.events_json)
    
    @classmethod
    def from_events(cls, activity_id: int, events: list[dict[str, Any]]) -> Self:
        """Create a recording from a list of rrweb events."""
        return cls(
            activity_id=activity_id,
            events_json=json.dumps(events),
            event_count=len(events),
            start_timestamp=events[0]["timestamp"] if events else 0,
            end_timestamp=events[-1]["timestamp"] if events else 0
        )
