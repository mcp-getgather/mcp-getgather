from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from getgather.database.repositories.activity_repository import Activity
from getgather.database.repositories.rrweb_recordings_repository import RRWebRecording


class ActivityWithCount(BaseModel):
    """Activity with recording count."""

    id: int | None
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None
    execution_time_ms: int | None
    created_at: datetime | None
    recording_count: int


class ActivitiesResponse(BaseModel):
    """Response for activities endpoint."""
    activities: list[ActivityWithCount]


class RecordingResponse(BaseModel):
    """Response for recording endpoint."""
    events: list[dict[str, Any]]


router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/", response_model=ActivitiesResponse)
async def get_activities() -> ActivitiesResponse:
    """Get all activities with recording counts."""
    activities = Activity.get_all()
    recording_counts = RRWebRecording.get_recording_counts()

    # Add recording count to each activity
    activities_with_counts: list[ActivityWithCount] = []
    for activity in activities:
        activity_data = activity.model_dump()
        activity_data["recording_count"] = recording_counts.get(activity.id or 0, 0)
        activities_with_counts.append(ActivityWithCount(**activity_data))

    return ActivitiesResponse(activities=activities_with_counts)


@router.get("/recordings", response_model=RecordingResponse)
async def get_recording(activity_id: int) -> RecordingResponse:
    """Get rrweb events for a specific activity."""
    recording = RRWebRecording.get_by_activity_id(activity_id)
    if not recording:
        raise HTTPException(
            status_code=404, detail=f"No recording found for activity {activity_id}"
        )

    return RecordingResponse(events=recording.events)
