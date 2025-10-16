from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

wayfair_mcp = BrandMCPBase(brand_id="wayfair", name="Wayfair MCP")


@wayfair_mcp.tool(tags={"private"})
async def get_order_history() -> dict[str, Any]:
    """Get order history of wayfair."""
    return await extract()
