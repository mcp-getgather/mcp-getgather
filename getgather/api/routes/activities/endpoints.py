from fastapi import APIRouter, HTTPException

from getgather.activity import Activity, activity_manager

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/")
async def get_activities() -> list[Activity]:
    """Get all activities ordered by start_time descending."""
    return await activity_manager.get_all_activities()


@router.get("/{activity_id}")
async def get_activity(activity_id: str) -> Activity:
    """Get a specific activity by ID."""
    activity = await activity_manager.get_activity(activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return activity
