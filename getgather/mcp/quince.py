from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

quince_mcp = GatherMCP(brand_id="quince", name="Quince MCP")


@quince_mcp.tool
async def get_orders() -> dict[str, Any]:
    """Get orders of quince."""
    return await dpage_mcp_tool("https://www.quince.com/account/my-orders-returns", "quince_orders")
