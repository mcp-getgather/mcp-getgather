from typing import Any

from getgather.database.connection import fetch_one
from getgather.database.models import RRWebRecording


class RRWebRecordingsRepository:
    """Repository for managing rrweb recordings."""

    @staticmethod
    def get_by_activity_id(activity_id: int) -> RRWebRecording | None:
        """Get a recording by activity ID."""
        query = "SELECT * FROM rrweb_recordings WHERE activity_id = ?"
        if row := fetch_one(query, (activity_id,)):
            return RRWebRecording.model_validate(row)
        return None

    @staticmethod
    def create_recording(activity_id: int, events: list[dict[str, Any]]) -> RRWebRecording:
        """Create a new recording from rrweb events."""
        recording = RRWebRecording.from_events(activity_id, events)
        recording.add()
        return recording

    @staticmethod
    def get_events_for_activity(activity_id: int) -> list[dict[str, Any]] | None:
        """Get the parsed events for an activity."""
        if recording := RRWebRecordingsRepository.get_by_activity_id(activity_id):
            return recording.events
        return None