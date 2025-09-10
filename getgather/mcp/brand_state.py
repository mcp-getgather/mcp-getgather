from getgather.mcp.persist import ModelWithAuth, PersistentStoreWithAuth


class BrandState(ModelWithAuth):
    """JSON-persisted brand state record."""

    brand_id: str
    browser_profile_id: str


class BrandStateStore(PersistentStoreWithAuth[BrandState]):
    _file_name: str = "brand_states.json"
    _row_model: type[BrandState] = BrandState
    _key_field: str = "brand_id"


brand_state_manager = BrandStateStore()
