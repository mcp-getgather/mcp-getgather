from datetime import datetime
from typing import Self

from getgather.database.models import DBModel
from getgather.database.connection import fetch_all


class Activity(DBModel):
    """Activity record model."""

    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None

    table_name = "activities"

    @classmethod
    def get_all(cls) -> list[Self]:
        """Get all activities ordered by start_time descending."""
        query = f"SELECT * FROM {cls.table_name} ORDER BY start_time DESC"
        rows = fetch_all(query)
        return [cls.model_validate(row) for row in rows]

    @classmethod
    def update_end_time(cls, id: int, end_time: datetime) -> None:
        """Update the end time of an activity."""
        if not cls.id:
            raise ValueError(f"Activity {cls.id} not found")

        activity = cls.get(id)
        if not activity:
            raise ValueError(f"Activity {id} not found")

        execution_time_ms = int((end_time - activity.start_time).total_seconds() * 1000)
        cls.update(
            id,
            {
                "end_time": end_time,
                "execution_time_ms": execution_time_ms,
            },
        )
