from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

wayfair_mcp = GatherMCP(brand_id="wayfair", name="Wayfair MCP")


@wayfair_mcp.tool
async def get_order_history() -> dict[str, Any]:
    """Get order history of Wayfair."""
    return await dpage_mcp_tool(
        "https://www.wayfair.com/session/secure/account/order_search.php", "wayfair_order_history"
    )
