from fastapi import APIRouter, HTTPException

from getgather.database.repositories.activity_repository import Activity
from getgather.database.repositories.rrweb_recordings_repository import RRWebRecordingsRepository

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/")
async def get_activities():
    """Get all activities with recording counts."""
    activities = Activity.get_all()
    recording_counts = RRWebRecordingsRepository.get_recording_counts()
    
    # Add recording count to each activity
    activities_with_counts = []
    for activity in activities:
        activity_dict = activity.model_dump() if hasattr(activity, 'model_dump') else activity.__dict__
        activity_dict['recording_count'] = recording_counts.get(activity.id, 0)
        activities_with_counts.append(activity_dict)
    
    return {"activities": activities_with_counts}


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