from typing import Any

from getgather.mcp.dpage import zen_dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

alfagift_mcp = GatherMCP(brand_id="alfagift", name="Alfagift MCP")

@alfagift_mcp.tool
async def get_order_sent() -> dict[str, Any]:
    """Get order sent alfagift."""
    return await zen_dpage_mcp_tool("https://alfagift.id/order-sent", "alfagift_order_sent")

@alfagift_mcp.tool
async def get_cart() -> dict[str, Any]:
    """Get cart alfagift."""
    return await zen_dpage_mcp_tool("https://alfagift.id/cart", "alfagift_cart")