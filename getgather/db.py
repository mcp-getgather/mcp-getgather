import json
import threading
from pathlib import Path
from typing import Any

from getgather.config import settings


class DatabaseManager:
    """JSON file-based key-value database management."""

    def __init__(self, json_file_path: Path):
        self.json_file_path = json_file_path
        self.data: None | dict[str, Any] = None
        self._lock = threading.RLock()

    def _load_data(self) -> dict[str, Any]:
        """Load data from JSON file."""
        if not self.json_file_path.exists():
            return {}

        try:
            with open(self.json_file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
        except (json.JSONDecodeError, OSError):
            # Handle corrupted JSON or file access issues
            return {}

        return data

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save data to JSON file."""
        # Ensure parent directory exists
        self.json_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.json_file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def get(self, key: str) -> Any:
        """Get a value by key."""
        with self._lock:
            if not self.data:
                self.data = self._load_data()

            return self.data.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set a value by key."""
        with self._lock:
            if not self.data:
                self.data = self._load_data()

            self.data[key] = value
            self._save_data(self.data)


# Global instance
db_manager = DatabaseManager(settings.db_json_path)
