from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

wayfair_mcp = GatherMCP(brand_id="wayfair", name="Wayfair MCP")


@wayfair_mcp.tool
async def dpage_get_order_history(page_number: int = 1) -> dict[str, Any]:
    """Get order history of wayfair."""
    return await dpage_mcp_tool(
        f"https://www.wayfair.com/session/secure/account/order_search.php?page={page_number}",
        "wayfair_order_history",
    )
