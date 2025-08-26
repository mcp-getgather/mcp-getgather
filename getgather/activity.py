import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import AsyncGenerator

from pydantic import BaseModel, Field

from getgather.db import db_manager


class Activity(BaseModel):
    """JSON-persisted activity record."""

    id: str
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    has_recording: bool | None = None


class ActivityManager:
    """Activity management."""

    def _load_activities(self) -> list[Activity]:
        """Load activities from database."""
        activities_data = db_manager.get("activities")
        if not activities_data:
            return []

        return [Activity.model_validate(activity_data) for activity_data in activities_data]

    def _save_activities(self, activities: list[Activity]) -> None:
        """Save activities to database."""
        data = [activity.model_dump() for activity in activities]
        db_manager.set("activities", data)

    async def create_activity(self, brand_id: str, name: str, start_time: datetime) -> str:
        """Create a new activity and return its ID."""
        activities = self._load_activities()

        activity_id = uuid.uuid4().hex
        activity = Activity(id=activity_id, brand_id=brand_id, name=name, start_time=start_time)
        activities.append(activity)

        self._save_activities(activities)
        return activity_id

    async def update_end_time(self, activity_id: str, end_time: datetime) -> None:
        """Update the end time of an activity."""
        activities = self._load_activities()

        # Find the activity
        activity = None
        for act in activities:
            if act.id == activity_id:
                activity = act
                break

        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        # Update the activity fields directly
        activity.end_time = end_time
        activity.execution_time_ms = int((end_time - activity.start_time).total_seconds() * 1000)

        self._save_activities(activities)

    async def get_activity(self, activity_id: str) -> Activity | None:
        """Get an activity by ID."""
        activities = self._load_activities()
        for activity in activities:
            if activity.id == activity_id:
                return activity
        return None

    async def get_all_activities(self) -> list[Activity]:
        """Get all activities ordered by start_time descending."""
        activities = self._load_activities()
        return sorted(activities, key=lambda a: a.start_time, reverse=True)


# Global instance
activity_manager = ActivityManager()

# Context variable for active activity tracking
active_activity_ctx: ContextVar[Activity | None] = ContextVar("active_activity", default=None)


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[str, None]:
    """Context manager for tracking activity."""
    activity_id = await activity_manager.create_activity(
        brand_id=brand_id,
        name=name,
        start_time=datetime.now(UTC),
    )

    # Get the activity object and set it in the context variable
    activity_obj = await activity_manager.get_activity(activity_id)
    token = active_activity_ctx.set(activity_obj)

    try:
        yield activity_id
    finally:
        # Reset the context variable
        active_activity_ctx.reset(token)
        await activity_manager.update_end_time(
            activity_id=activity_id,
            end_time=datetime.now(UTC),
        )
