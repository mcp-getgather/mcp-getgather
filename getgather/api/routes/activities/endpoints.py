from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from getgather.activity import activity_manager
from getgather.rrweb.event_manager import rrweb_event_manager


class ActivityResponse(BaseModel):
    """Activity response model for API."""

    id: int
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None
    created_at: datetime
    recording_count: int = 0


class RecordingResponse(BaseModel):
    """Recording response model for API."""

    activity_id: int
    events: list[dict[str, Any]]


router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/", response_model=list[ActivityResponse])
async def get_activities():
    """Get all activities ordered by start_time descending."""
    activities = await activity_manager.get_all_activities()
    recording_counts = await rrweb_event_manager.get_recording_counts()

    return [
        ActivityResponse(
            id=activity.id,
            brand_id=activity.brand_id,
            name=activity.name,
            start_time=activity.start_time,
            end_time=activity.end_time,
            execution_time_ms=activity.execution_time_ms,
            created_at=activity.created_at,
            recording_count=recording_counts.get(activity.id, 0),
        )
        for activity in activities
    ]


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(activity_id: int):
    """Get a specific activity by ID."""
    activity = await activity_manager.get_activity(activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    recording_counts = await rrweb_event_manager.get_recording_counts()

    return ActivityResponse(
        id=activity.id,
        brand_id=activity.brand_id,
        name=activity.name,
        start_time=activity.start_time,
        end_time=activity.end_time,
        execution_time_ms=activity.execution_time_ms,
        created_at=activity.created_at,
        recording_count=recording_counts.get(activity.id, 0),
    )


@router.get("/{activity_id}/recordings", response_model=RecordingResponse)
async def get_recording(activity_id: int):
    """Get rrweb events for a specific activity."""
    # Verify activity exists
    activity = await activity_manager.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get recording events
    events = await rrweb_event_manager.get_events_by_activity_id(activity_id)

    return RecordingResponse(
        activity_id=activity_id,
        events=events,
    )
