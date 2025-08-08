from datetime import datetime

from getgather.database.models import DBModel


class ActivityRepository(DBModel):
    """Activity record model."""

    _table_name = "activities"

    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None

    @classmethod
    def create(
        cls,
        brand_id: str,
        name: str,
        start_time: datetime,
    ) -> int:
        """Insert a new activity and return its ID."""
        activity = cls(
            brand_id=brand_id,
            name=name,
            start_time=start_time,
        )
        return cls.add(activity)

    @classmethod
    def update_end_time(cls, activity_id: int, end_time: datetime) -> None:
        """Update the end time of an activity."""
        activity = cls.get(activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        execution_time_ms = int((end_time - activity.start_time).total_seconds() * 1000)
        cls.update(
            activity_id,
            {
                "end_time": end_time,
                "execution_time_ms": execution_time_ms,
            },
        )
