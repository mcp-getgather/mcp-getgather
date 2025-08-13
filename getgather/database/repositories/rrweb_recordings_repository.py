import json
from typing import Any, Self

from getgather.database.connection import execute_insert, fetch_all, fetch_one
from getgather.database.models import DBModel
from getgather.logs import logger


class RRWebRecording(DBModel):
    """rrweb recording model for storing browser automation replays."""

    table_name = "rrweb_recordings"

    activity_id: int
    events_json: str
    event_count: int
    start_timestamp: int
    end_timestamp: int

    @property
    def events(self) -> list[dict[str, Any]]:
        """Parse and return the events as a Python list."""
        return json.loads(self.events_json)

    @classmethod
    def from_events(cls, activity_id: int, events: list[dict[str, Any]]) -> Self:
        """Create a recording from a list of rrweb events."""
        return cls(
            activity_id=activity_id,
            events_json=json.dumps(events),
            event_count=len(events),
            start_timestamp=events[0]["timestamp"] if events else 0,
            end_timestamp=events[-1]["timestamp"] if events else 0,
        )

    @classmethod
    def get_by_activity_id(cls, activity_id: int) -> Self | None:
        """Get a recording by activity ID."""
        query = f"SELECT * FROM {cls.table_name} WHERE activity_id = ?"
        if row := fetch_one(query, (activity_id,)):
            return cls.model_validate(row)
        return None

    @classmethod
    def create_recording(cls, activity_id: int, events: list[dict[str, Any]]) -> Self:
        """Create a new recording from rrweb events."""
        recording = cls.from_events(activity_id, events)
        recording_id = cls.add(recording)
        recording.id = recording_id
        return recording

    @classmethod
    def get_events_for_activity(cls, activity_id: int) -> list[dict[str, Any]] | None:
        """Get the parsed events for an activity."""
        if recording := cls.get_by_activity_id(activity_id):
            return recording.events
        return None

    @classmethod
    def get_recording_counts(cls) -> dict[int, int]:
        """Get recording event counts for all activities."""
        query = f"SELECT activity_id, event_count FROM {cls.table_name}"
        rows = fetch_all(query)
        return {row["activity_id"]: row["event_count"] for row in rows}

    @classmethod
    def add_event_to_activity(cls, activity_id: int, event: dict[str, Any]) -> None:
        """Add a single event to an activity's recording."""
        logger.info(
            f"add_event_to_activity called for activity {activity_id}, event type: {event.get('type')}"
        )

        # Check if recording exists
        recording = cls.get_by_activity_id(activity_id)

        if recording:
            logger.info(
                f"Found existing recording for activity {activity_id} with {len(recording.events)} events"
            )
            # Append event to existing recording
            events = recording.events
            events.append(event)

            # Update the recording
            if recording.id is not None:
                cls.update(
                    recording.id,
                    {
                        "events_json": json.dumps(events),
                        "event_count": len(events),
                        "end_timestamp": event.get("timestamp", 0),
                    },
                )
            logger.info(
                f"Updated recording for activity {activity_id}, now has {len(events)} events"
            )
        else:
            logger.info(f"Creating new recording for activity {activity_id}")
            # Create new recording with first event
            events = [event]
            query = f"""
                INSERT INTO {cls.table_name} (activity_id, events_json, event_count, start_timestamp, end_timestamp)
                VALUES (?, ?, ?, ?, ?)
            """
            execute_insert(
                query,
                (
                    activity_id,
                    json.dumps(events),
                    1,
                    event.get("timestamp", 0),
                    event.get("timestamp", 0),
                ),
            )
            logger.info(f"Created new recording for activity {activity_id} with first event")
