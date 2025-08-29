from pydantic import BaseModel

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.db import db_manager


class BrandState(BaseModel):
    """JSON-persisted brand state record."""

    brand_id: str
    browser_profile_id: str
    is_connected: bool


class BrandStateManager:
    """Brand state management."""

    def _load_brand_states(self) -> list[BrandState]:
        """Load brand states from database."""
        brand_states_data = db_manager.get("brand_states")
        if not brand_states_data:
            return []

        return [
            BrandState.model_validate(brand_state_data) for brand_state_data in brand_states_data
        ]

    def _save_brand_states(self, brand_states: list[BrandState]) -> None:
        """Save brand states to database."""
        data = [brand_state.model_dump() for brand_state in brand_states]
        db_manager.set("brand_states", data)

    def get_by_brand_id(self, brand_id: BrandIdEnum) -> BrandState | None:
        """Get a brand state by its brand ID."""
        brand_states = self._load_brand_states()
        for brand_state in brand_states:
            if brand_state.brand_id == brand_id:
                return brand_state
        return None

    def update_is_connected(self, brand_id: BrandIdEnum, is_connected: bool) -> None:
        """Update the is_connected status for a brand."""
        brand_states = self._load_brand_states()

        # Find the brand state
        brand_state = None
        for bs in brand_states:
            if bs.brand_id == brand_id:
                brand_state = bs
                break

        if not brand_state:
            raise ValueError(f"Brand state {brand_id} not found")

        # Update the brand state field directly
        brand_state.is_connected = is_connected

        self._save_brand_states(brand_states)

    def is_brand_connected(self, brand_id: BrandIdEnum) -> bool:
        """Check if a brand is connected."""
        state = self.get_by_brand_id(BrandIdEnum(brand_id))
        return state.is_connected if state else False

    def get_browser_profile_id(self, brand_id: BrandIdEnum | str) -> str | None:
        """Get the browser profile ID for a brand."""
        state = self.get_by_brand_id(BrandIdEnum(brand_id))
        return state.browser_profile_id if state else None

    def add(self, brand_state: BrandState) -> None:
        """Add a new brand state."""
        brand_states = self._load_brand_states()
        brand_states.append(brand_state)
        self._save_brand_states(brand_states)


# Global instance
brand_state_manager = BrandStateManager()
