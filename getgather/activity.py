import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncGenerator

from pydantic import BaseModel, Field

from getgather.config import settings


class Activity(BaseModel):
    """JSON-persisted activity record."""

    id: str
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class Activities(BaseModel):
    """Collection of activities with helper methods."""

    activities: list[Activity] = Field(default_factory=lambda: [])

    def add(self, activity: Activity) -> None:
        """Add an activity to the collection."""
        self.activities.append(activity)

    def get_by_id(self, activity_id: str) -> Activity | None:
        """Get an activity by ID."""
        for activity in self.activities:
            if activity.id == activity_id:
                return activity
        return None

    def get_all_sorted(self) -> list[Activity]:
        """Get all activities sorted by start_time descending."""
        return sorted(self.activities, key=lambda a: a.start_time, reverse=True)

    def update_activity(self, activity: Activity) -> bool:
        """Update an activity. Returns True if found and updated."""
        for i, existing_activity in enumerate(self.activities):
            if existing_activity.id == activity.id:
                self.activities[i] = activity
                return True
        return False


class ActivityManager:
    """JSON file-based activity management."""

    def __init__(self, json_file_path: Path):
        self.json_file_path = json_file_path

    def _load_activities(self) -> Activities:
        """Load activities from JSON file."""
        if not self.json_file_path.exists():
            return Activities()
        
        try:
            with open(self.json_file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return Activities()
                data = json.loads(content)

            return Activities.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load activities from {self.json_file_path}: {e}")
            return Activities()

    def _save_activities(self, activities: Activities) -> None:
        """Save activities to JSON file."""
        try:
            # Ensure parent directory exists
            self.json_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.json_file_path, "w") as f:
                f.write(activities.model_dump_json(indent=2))
        except (OSError, IOError) as e:
            # Log error but don't raise - allows app to continue working
            # In a real app, you might want to use proper logging here
            print(f"Warning: Failed to save activities to {self.json_file_path}: {e}")

    async def create_activity(self, brand_id: str, name: str, start_time: datetime) -> str:
        """Create a new activity and return its ID."""
        activities = self._load_activities()
        
        activity_id = uuid.uuid4().hex

        activity = Activity(id=activity_id, brand_id=brand_id, name=name, start_time=start_time)
        activities.add(activity)
        
        self._save_activities(activities)
        return activity_id

    async def update_end_time(self, activity_id: str, end_time: datetime) -> None:
        """Update the end time of an activity."""
        activities = self._load_activities()
        
        activity = activities.get_by_id(activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        
        # Update the activity fields directly
        activity.end_time = end_time
        activity.execution_time_ms = int((end_time - activity.start_time).total_seconds() * 1000)
        
        activities.update_activity(activity)
        self._save_activities(activities)

    async def get_activity(self, activity_id: str) -> Activity | None:
        """Get an activity by ID."""
        activities = self._load_activities()
        return activities.get_by_id(activity_id)

    async def get_all_activities(self) -> list[Activity]:
        """Get all activities ordered by start_time descending."""
        activities = self._load_activities()
        return activities.get_all_sorted()


# Global instance
activity_manager = ActivityManager(settings.activities_json_path)


@asynccontextmanager
async def activity(name: str, brand_id: str = "") -> AsyncGenerator[None, None]:
    """Context manager for tracking activity."""
    activity_id = await activity_manager.create_activity(
        brand_id=brand_id,
        name=name,
        start_time=datetime.now(UTC),
    )
    try:
        yield
    finally:
        await activity_manager.update_end_time(
            activity_id=activity_id,
            end_time=datetime.now(UTC),
        )
