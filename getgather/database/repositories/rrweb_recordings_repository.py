import json
from typing import Any

from getgather.database.connection import execute_insert, fetch_one
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

    @staticmethod
    def add_event_to_activity(activity_id: int, event: dict[str, Any]) -> None:
        """Add a single event to an activity's recording."""
        # Check if recording exists
        recording = RRWebRecordingsRepository.get_by_activity_id(activity_id)
        
        if recording:
            # Append event to existing recording
            events = recording.events
            events.append(event)
            
            # Update the recording
            query = """
                UPDATE rrweb_recordings 
                SET events_json = ?, event_count = ?, end_timestamp = ?
                WHERE activity_id = ?
            """
            execute_insert(query, (
                json.dumps(events),
                len(events),
                event.get("timestamp", 0),
                activity_id
            ))
        else:
            # Create new recording with first event
            events = [event]
            query = """
                INSERT INTO rrweb_recordings (activity_id, events_json, event_count, start_timestamp, end_timestamp)
                VALUES (?, ?, ?, ?, ?)
            """
            execute_insert(query, (
                activity_id,
                json.dumps(events),
                1,
                event.get("timestamp", 0),
                event.get("timestamp", 0)
            ))