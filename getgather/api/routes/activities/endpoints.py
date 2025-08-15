from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from getgather.activity import activity_manager


class ActivityResponse(BaseModel):
    """Activity response model for API."""
    id: int
    brand_id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime


router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/", response_model=List[ActivityResponse])
async def get_activities():
    """Get all activities ordered by start_time descending."""
    activities = await activity_manager.get_all_activities()
    
    return [
        ActivityResponse(
            id=activity.id,
            brand_id=activity.brand_id,
            name=activity.name,
            start_time=activity.start_time,
            end_time=activity.end_time,
            execution_time_ms=activity.execution_time_ms,
            created_at=activity.created_at,
        )
        for activity in activities
    ]


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(activity_id: int):
    """Get a specific activity by ID."""
    activity = await activity_manager.get_activity(activity_id)
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return ActivityResponse(
        id=activity.id,
        brand_id=activity.brand_id,
        name=activity.name,
        start_time=activity.start_time,
        end_time=activity.end_time,
        execution_time_ms=activity.execution_time_ms,
        created_at=activity.created_at,
    )