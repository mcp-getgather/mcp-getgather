from pydantic import BaseModel

from getgather.mcp.persist import PersistentStore


class BrandState(BaseModel):
    """JSON-persisted brand state record."""

    brand_id: str
    browser_profile_id: str
    is_connected: bool


class BrandStateStore(PersistentStore[BrandState]):
    _file_name: str = "brand_states.json"
    _row_model: type[BrandState] = BrandState
    _key_field: str = "brand_id"


brand_state_manager = BrandStateStore()
