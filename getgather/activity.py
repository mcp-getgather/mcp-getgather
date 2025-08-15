import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import AsyncGenerator


@dataclass
class Activity:
    """In-memory activity record."""

    id: int
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now())


class ActivityManager:
    """Async-safe in-memory activity management."""

    def __init__(self):
        self._activities: dict[int, Activity] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()

    async def create_activity(self, brand_id: str, name: str, start_time: datetime) -> int:
        """Create a new activity and return its ID."""
        async with self._lock:
            activity_id = self._next_id
            self._next_id += 1

            activity = Activity(id=activity_id, brand_id=brand_id, name=name, start_time=start_time)

            self._activities[activity_id] = activity
            return activity_id

    async def update_end_time(self, activity_id: int, end_time: datetime) -> None:
        """Update the end time of an activity."""
        async with self._lock:
            if activity_id not in self._activities:
                raise ValueError(f"Activity {activity_id} not found")

            activity = self._activities[activity_id]
            activity.end_time = end_time
            activity.execution_time_ms = int(
                (end_time - activity.start_time).total_seconds() * 1000
            )

    async def get_activity(self, activity_id: int) -> Activity | None:
        """Get an activity by ID."""
        async with self._lock:
            return self._activities.get(activity_id)

    async def get_all_activities(self) -> list[Activity]:
        """Get all activities ordered by start_time descending."""
        async with self._lock:
            return sorted(self._activities.values(), key=lambda a: a.start_time, reverse=True)


# Global instance
activity_manager = ActivityManager()

# Context variable for active activity tracking
active_activity_ctx: ContextVar[Activity | None] = ContextVar("active_activity", default=None)


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[int, None]:
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
