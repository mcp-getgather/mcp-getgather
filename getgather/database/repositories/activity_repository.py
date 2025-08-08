from datetime import datetime

from getgather.database.models import DBModel


class ActivityRepository(DBModel):
    """Activity record model."""

    activity_id: int | None
    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None

    @property
    def table_name(self):
        return "activities"

    def create(self) -> int:
        """Insert a new activity and return its ID."""
        self.activity_id = self.add()
        return self.activity_id

    def update_end_time(self, end_time: datetime) -> None:
        """Update the end time of an activity."""
        if not self.activity_id:
            raise ValueError(f"Activity {self.activity_id} not found")

        activity = self.get(self.activity_id)
        if not activity:
            raise ValueError(f"Activity {self.activity_id} not found")

        execution_time_ms = int((end_time - activity.start_time).total_seconds() * 1000)
        self.update(
            self.activity_id,
            {
                "end_time": end_time,
                "execution_time_ms": execution_time_ms,
            },
        )
