"""Context variables for tracking state across async operations."""

from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import AsyncGenerator

from getgather.database.repositories.activity_repository import Activity

# Context variable to track the current activity across async calls
current_activity: ContextVar[Activity | None] = ContextVar("current_activity", default=None)


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[None, None]:
    """Context manager for tracking activity."""
    activity = Activity(
        brand_id=brand_id,
        name=name,
        start_time=datetime.now(UTC),
    )
    activity_id = Activity.add(activity)

    # Update the activity object with the assigned ID
    activity.id = activity_id

    # Set the activity in context
    token = current_activity.set(activity)
    try:
        yield
    finally:
        # Reset the context and update end time
        current_activity.reset(token)
        Activity.update_end_time(
            id=activity_id,
            end_time=datetime.now(UTC),
        )
