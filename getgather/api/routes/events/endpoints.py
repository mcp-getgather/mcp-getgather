from fastapi import APIRouter, HTTPException

from getgather.database.repositories.rrweb_recordings_repository import RRWebRecordingsRepository

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
async def get_events(activity_id: int):
    """Get rrweb events for a specific activity."""
    recording = RRWebRecordingsRepository.get_by_activity_id(activity_id)
    if not recording:
        raise HTTPException(
            status_code=404, 
            detail=f"No recording found for activity {activity_id}"
        )
    
    return {"events": recording.events}