from typing import Any

from fastmcp.server.dependencies import get_context, get_http_headers
from pydantic import BaseModel

from getgather.mcp.persist import PersistentStore


def _is_custom_app() -> bool:
    headers = get_http_headers(include_all=True)
    return headers.get("x-getgather-custom-app") is not None


class BrandState(BaseModel):
    """JSON-persisted brand state record."""

    brand_id: str
    browser_profile_id: str
    is_connected: bool
    mcp_session_id: str | None = None


class BrandStateStore(PersistentStore[BrandState]):
    _file_name: str = "brand_states.json"
    _row_model: type[BrandState] = BrandState
    _key_field: str = "brand_id"

    def key_for_retrieval(self, model_key: str) -> Any:
        if _is_custom_app():
            return (get_context().session_id, model_key)
        return model_key

    def row_key_for_index(self, row: BrandState) -> Any:
        if _is_custom_app():
            return (get_context().session_id, getattr(row, self._key_field))
        return getattr(row, self._key_field)

    def get_all(self) -> list[BrandState]:
        rows = super().get_all()
        if _is_custom_app():
            return list(filter(lambda a: a.mcp_session_id == get_context().session_id, rows))
        return rows

    def add(self, row: BrandState) -> BrandState:
        if _is_custom_app():
            row.mcp_session_id = get_context().session_id
        return super().add(row)


brand_state_manager = BrandStateStore()
