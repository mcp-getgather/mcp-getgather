from getgather.mcp.persist import ModelWithAuth, PersistentStoreWithAuth


class BrandState(ModelWithAuth):
    """JSON-persisted brand state record."""

    brand_id: str
    browser_profile_id: str
    is_connected: bool
    mcp_session_id: str | None = None


class BrandStateStore(PersistentStoreWithAuth[BrandState]):
    _file_name: str = "brand_states.json"
    _row_model: type[BrandState] = BrandState
    _key_field: str = "brand_id"

    def get_by_mcp_session_id(self, mcp_session_id: str) -> BrandState | None:
        """Get brand state by MCP session ID."""
        if not self._indexes:
            self.load()

        # Search through all rows for matching mcp_session_id
        for row in self.get_all():
            if row.mcp_session_id == mcp_session_id:
                return row
        return None


brand_state_manager = BrandStateStore()
