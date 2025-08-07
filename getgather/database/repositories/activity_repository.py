from datetime import datetime
from typing import TypedDict

from getgather.database.connection import execute_insert, execute_query, fetch_all, fetch_one


class Activity(TypedDict):
    """Type definition for activity records."""

    id: int
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None
    execution_time_ms: int | None
    created_at: datetime


def insert(
    brand_id: str,
    name: str,
    start_time: datetime,
) -> int:
    """Insert a new activity and return its ID."""
    query = """
        INSERT INTO activities (
            brand_id, name, start_time
        ) VALUES (?, ?, ?)
    """
    params = (
        brand_id,
        name,
        start_time.isoformat(),
    )
    return execute_insert(query, params)


def update(activity_id: int, end_time: datetime) -> None:
    """Update the end time of an activity."""
    query = """
        UPDATE activities SET end_time = ?, execution_time_ms = ? WHERE id = ?
    """
    activity = get_activity(activity_id)
    start_time = (
        datetime.fromisoformat(activity["start_time"])
        if isinstance(activity["start_time"], str)
        else activity["start_time"]
    )
    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
    execute_query(query, (end_time.isoformat(), execution_time_ms, activity_id))


def get_activity(activity_id: int) -> Activity:
    """Get an activity by its ID."""
    query = """
        SELECT * FROM activities WHERE id = ?
    """
    return fetch_one(query, (activity_id,))  # type: ignore


def get_activities(limit: int = 100) -> list[Activity]:
    """Get recent activities."""
    query = """
        SELECT * FROM activities
        ORDER BY created_at DESC
        LIMIT ?
    """
    return fetch_all(query, (limit,))  # type: ignore
