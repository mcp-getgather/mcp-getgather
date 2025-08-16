from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

audible_mcp = BrandMCPBase(brand_id="audible", name="Audible MCP")


@audible_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get book list from Audible.com."""
    return await extract()
