from fastapi import APIRouter, HTTPException

from getgather.activity import Activity, activity_manager
from getgather.rrweb import Recording, rrweb_manager

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/")
async def get_activities() -> list[Activity]:
    """Get all activities ordered by start_time descending."""
    activities = await activity_manager.get_all_activities()

    # Add recording status to each activity
    for activity in activities:
        activity.has_recording = await rrweb_manager.activity_has_recording(activity.id)

    return activities


@router.get("/{activity_id}/recordings")
async def get_recording(activity_id: str) -> Recording:
    """Get rrweb events for a specific activity."""
    # Verify activity exists
    activity = await activity_manager.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get recording events
    recording = await rrweb_manager.get_recording_by_activity_id(activity_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording
