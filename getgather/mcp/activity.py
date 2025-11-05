import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncGenerator

from pydantic import BaseModel, Field, computed_field

from getgather.mcp.persist import PersistentStore


class Activity(BaseModel):
    """JSON-persisted activity record."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    has_recording: bool | None = None

    @computed_field
    @property
    def execution_time_ms(self) -> int | None:
        if self.end_time is None:
            return None
        return int((self.end_time - self.start_time).total_seconds() * 1000)


class ActivityManager(PersistentStore[Activity]):
    _file_name: str = "activities.json"
    _row_model: type[Activity] = Activity
    _key_field: str = "id"

    def get_all(self) -> list[Activity]:
        """Get all activities ordered by start_time descending."""
        rows = super().get_all()
        return sorted(rows, key=lambda a: a.start_time, reverse=True)


activity_manager = ActivityManager()


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[str, None]:
    """Context manager for tracking activity."""
    activity = Activity(brand_id=brand_id, name=name, start_time=datetime.now(UTC))
    activity_manager.add(activity)
    try:
        yield activity.id
    finally:
        activity.end_time = datetime.now(UTC)
        activity_manager.update(activity)
