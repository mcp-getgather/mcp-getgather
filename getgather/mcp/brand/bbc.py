from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

bbc_mcp = BrandMCPBase(brand_id="bbc", name="BBC MCP")


@bbc_mcp.tool(tags={"private"})
async def get_bookmarks() -> dict[str, Any]:
    """Get bookmarks of bbc."""
    return await extract(brand_id=bbc_mcp.brand_id)
