from typing import Any

from getgather.mcp.dpage import zen_dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

horizonhobby_mcp = GatherMCP(brand_id="horizonhobby", name="Horizon Hobby MCP")


@horizonhobby_mcp.tool
async def get_cart() -> dict[str, Any]:
    """Get the list of cart from Horizon Hobby"""
    return await zen_dpage_mcp_tool("https://www.horizonhobby.com/cart", "horizonhobby_cart")
