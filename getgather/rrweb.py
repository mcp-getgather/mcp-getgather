import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from getgather.config import settings


class Recording(BaseModel):
    """Recording response model for API."""

    activity_id: str
    events: list[dict[str, Any]]


class RRWebManager:
    """Per-activity file-based RRWeb recording management."""

    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir

    def _get_activity_file_path(self, activity_id: str) -> Path:
        """Get the file path for an activity's recording."""
        return self.recordings_dir / f"activity_{activity_id}.json"

    def _load_activity_recording(self, activity_id: str) -> Recording | None:
        """Load recording for a specific activity."""
        file_path = self._get_activity_file_path(activity_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return None
                data = json.loads(content)
                return Recording.model_validate(data)
        except (json.JSONDecodeError, OSError):
            return None

    def _save_activity_recording(self, recording: Recording) -> None:
        """Save recording for a specific activity."""
        file_path = self._get_activity_file_path(recording.activity_id)
        
        with open(file_path, "w") as f:
            json.dump(recording.model_dump(), f, indent=2, default=str)

    async def add_event(self, activity_id: str, event: dict[str, Any]) -> None:
        """Add an RRWeb event to an activity."""
        recording = self._load_activity_recording(activity_id)
        
        if recording:
            # Add event to existing recording
            recording.events.append(event)
        else:
            # Create new recording with this event
            recording = Recording(activity_id=activity_id, events=[event])
        
        self._save_activity_recording(recording)

    async def get_recording_by_activity_id(self, activity_id: str) -> Recording | None:
        """Get recording by activity ID."""
        return self._load_activity_recording(activity_id)
    
    async def activity_has_recording(self, activity_id: str) -> bool:
        """Check if activity has recording."""
        file_path = self._get_activity_file_path(activity_id)
        return file_path.exists()


# Global instance
rrweb_manager = RRWebManager(settings.recordings_dir)
