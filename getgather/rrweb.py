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
    """JSON file-based RRWeb recording management."""

    def __init__(self, json_file_path: Path):
        self.json_file_path = json_file_path

    def _load_recordings(self) -> list[Recording]:
        """Load recordings from JSON file."""
        if not self.json_file_path.exists():
            return []

        try:
            with open(self.json_file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
        except (json.JSONDecodeError, OSError):
            # Handle corrupted JSON or file access issues
            return []

        return [Recording.model_validate(recording_data) for recording_data in data]

    def _save_recordings(self, recordings: list[Recording]) -> None:
        """Save recordings to JSON file."""
        # Ensure parent directory exists
        self.json_file_path.parent.mkdir(parents=True, exist_ok=True)

        data = [recording.model_dump() for recording in recordings]
        with open(self.json_file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def add_event_to_recording(self, recording: Recording) -> None:
        """Add an RRWeb event to an activity."""
        recordings = self._load_recordings()
        
        # Find existing recording for this activity
        existing_recording = None
        for rec in recordings:
            if rec.activity_id == recording.activity_id:
                existing_recording = rec
                break
        
        if existing_recording:
            # Extend existing recording with new events
            existing_recording.events.extend(recording.events)
        else:
            # Add new recording
            recordings.append(recording)
        
        self._save_recordings(recordings)

    async def get_recording_by_activity_id(self, activity_id: str) -> Recording | None:
        """Get recording by activity ID."""
        recordings = self._load_recordings()
        for recording in recordings:
            if recording.activity_id == activity_id:
                return recording
        return None
    
    async def activity_has_recording(self, activity_id: str) -> bool:
        """Check if activity has recording."""
        recording = await self.get_recording_by_activity_id(activity_id)
        return recording is not None and len(recording.events) > 0


# Global instance
rrweb_manager = RRWebManager(settings.recordings_json_path)
