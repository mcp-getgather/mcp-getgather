import json
from pathlib import Path
from typing import Any

from getgather.config import settings


class DatabaseManager:
    """JSON file-based key-value database management."""

    def __init__(self, json_file_path: Path):
        self.json_file_path = json_file_path

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

    async def get(self, key: str) -> Any:
        """Get a value by key."""
        data = self._load_data()
        return data.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set a value by key."""
        data = self._load_data()
        data[key] = value
        self._save_data(data)

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed, False otherwise."""
        data = self._load_data()
        if key in data:
            del data[key]
            self._save_data(data)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        data = self._load_data()
        return key in data

    async def keys(self) -> list[str]:
        """Get all keys."""
        data = self._load_data()
        return list(data.keys())

    async def clear(self) -> None:
        """Clear all data."""
        self._save_data({})


# Global instance
db_manager = DatabaseManager(settings.db_json_path)
