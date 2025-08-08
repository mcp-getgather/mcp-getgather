from datetime import datetime

from getgather.database.models import DBModel


class Activity(DBModel):
    """Activity record model."""

    brand_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int | None = None

    @property
    def table_name(self):
        return "activities"

    def update_end_time(self, end_time: datetime) -> None:
        """Update the end time of an activity."""
        if not self.id:
            raise ValueError(f"Activity {self.id} not found")

        activity = self.get(self.id)
        if not activity:
            raise ValueError(f"Activity {self.id} not found")

        execution_time_ms = int((end_time - activity.start_time).total_seconds() * 1000)
        self.update(
            self.id,
            {
                "end_time": end_time,
                "execution_time_ms": execution_time_ms,
            },
        )
