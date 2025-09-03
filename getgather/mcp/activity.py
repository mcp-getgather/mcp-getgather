import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncGenerator

from pydantic import Field, computed_field

from getgather import rrweb
from getgather.mcp.auth import get_auth_user
from getgather.mcp.persist import ModelWithAuth, PersistentStoreWithAuth


class Activity(ModelWithAuth):
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


class ActivityManager(PersistentStoreWithAuth[Activity]):
    _file_name: str = "activities.json"
    _row_model: type[Activity] = Activity
    _key_field: str = "id"

    def get_all(self) -> list[Activity]:
        """Get all activities ordered by start_time descending."""
        user_login = get_auth_user().login
        self.load()
        return sorted(
            filter(lambda a: a.user_login == user_login, self.rows),
            key=lambda a: a.start_time,
            reverse=True,
        )


activity_manager = ActivityManager()


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[str, None]:
    """Context manager for tracking activity."""
    user_login = get_auth_user().login
    activity = Activity(
        brand_id=brand_id, name=name, start_time=datetime.now(UTC), user_login=user_login
    )
    activity_manager.add(activity)
    try:
        yield activity.id
    finally:
        await rrweb.rrweb_manager.save_recording(activity.id)
        activity.end_time = datetime.now(UTC)
        activity_manager.update(activity)
