from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

lenspure_mcp = GatherMCP(brand_id="lenspure", name="Lenspure MCP")


@lenspure_mcp.tool
async def get_order_history() -> dict[str, Any]:
    """Get order history of lenspure."""
    return await dpage_mcp_tool("https://www.lenspure.com/mporder/list", "lenspure_orders")
