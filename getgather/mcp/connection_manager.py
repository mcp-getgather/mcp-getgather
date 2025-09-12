"""Manages brand connection status for single-user setup."""

import json

from getgather.config import settings
from getgather.connectors.spec_loader import BrandIdEnum


class ConnectionManager:
    """Simple connection manager for single-user setup."""

    def __init__(self):
        self._file_path = settings.persistent_store_dir / "connections.json"
        self._connections: dict[str, bool] = self._load()

    def _load(self) -> dict[str, bool]:
        """Load connections from disk."""
        if self._file_path.exists():
            try:
                with open(self._file_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self) -> None:
        """Save connections to disk."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, "w") as f:
            json.dump(self._connections, f)

    def is_connected(self, brand_id: BrandIdEnum) -> bool:
        """Check if a brand is connected."""
        # Reload from disk to ensure we have the latest state
        self._connections = self._load()
        return self._connections.get(str(brand_id), False)

    def set_connected(self, brand_id: BrandIdEnum, connected: bool = True) -> None:
        """Mark a brand as connected or disconnected."""
        self._connections[str(brand_id)] = connected
        self._save()

    def disconnect(self, brand_id: BrandIdEnum) -> None:
        """Mark a brand as disconnected."""
        self.set_connected(brand_id, False)


# Global instance
connection_manager = ConnectionManager()
