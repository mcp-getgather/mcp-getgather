from fastapi import APIRouter, HTTPException

from getgather.activity import Activity, activity_manager

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/", response_model=list[Activity])
async def get_activities():
    """Get all activities ordered by start_time descending."""
    return await activity_manager.get_all_activities()


@router.get("/{activity_id}", response_model=Activity)
async def get_activity(activity_id: str):
    """Get a specific activity by ID."""
    activity = await activity_manager.get_activity(activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return activity
