from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

hardcover_mcp = BrandMCPBase(brand_id="hardcover", name="Hardcover MCP")


@hardcover_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get book list from Hardcover.app."""
    return await extract()
