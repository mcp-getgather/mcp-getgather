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



class ActivityManager:
    """JSON file-based activity management."""

    def __init__(self, json_file_path: Path):
        self.json_file_path = json_file_path

    def _load_activities(self) -> list[Activity]:
        """Load activities from JSON file."""
        if not self.json_file_path.exists():
            return []
        
        try:
            with open(self.json_file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)

            return [Activity.model_validate(activity_data) for activity_data in data]
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load activities from {self.json_file_path}: {e}")
            return []

    def _save_activities(self, activities: list[Activity]) -> None:
        """Save activities to JSON file."""
        try:
            # Ensure parent directory exists
            self.json_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = [activity.model_dump() for activity in activities]
            with open(self.json_file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, IOError) as e:
            # Log error but don't raise - allows app to continue working
            # In a real app, you might want to use proper logging here
            print(f"Warning: Failed to save activities to {self.json_file_path}: {e}")

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
