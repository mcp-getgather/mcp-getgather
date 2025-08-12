import json
from typing import Any

from getgather.database.connection import execute_insert, fetch_one
from getgather.database.models import RRWebRecording
from getgather.logs import logger


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
    def get_recording_counts() -> dict[int, int]:
        """Get recording event counts for all activities."""
        from getgather.database.connection import fetch_all
        query = "SELECT activity_id, event_count FROM rrweb_recordings"
        rows = fetch_all(query)
        return {row['activity_id']: row['event_count'] for row in rows}

    @staticmethod
    def add_event_to_activity(activity_id: int, event: dict[str, Any]) -> None:
        """Add a single event to an activity's recording."""
        logger.info(f"add_event_to_activity called for activity {activity_id}, event type: {event.get('type')}")
        
        # Check if recording exists
        recording = RRWebRecordingsRepository.get_by_activity_id(activity_id)
        
        if recording:
            logger.info(f"Found existing recording for activity {activity_id} with {len(recording.events)} events")
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
            logger.info(f"Updated recording for activity {activity_id}, now has {len(events)} events")
        else:
            logger.info(f"Creating new recording for activity {activity_id}")
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
            logger.info(f"Created new recording for activity {activity_id} with first event")