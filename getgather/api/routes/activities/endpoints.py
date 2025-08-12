from fastapi import APIRouter, HTTPException

from getgather.database.repositories.activity_repository import Activity
from getgather.database.repositories.rrweb_recordings_repository import RRWebRecordingsRepository

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/")
async def get_activities():
    """Get all activities."""
    activities = Activity.get_all()
    return {"activities": activities}


@router.get("/recordings")
async def get_recording(activity_id: int):
    """Get rrweb events for a specific activity."""
    recording = RRWebRecordingsRepository.get_by_activity_id(activity_id)
    if not recording:
        raise HTTPException(
            status_code=404, 
            detail=f"No recording found for activity {activity_id}"
        )
    
    return {"events": recording.events}