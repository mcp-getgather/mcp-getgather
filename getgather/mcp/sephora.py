from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

sephora_mcp = GatherMCP(brand_id="sephora", name="Sephora MCP")


@sephora_mcp.tool
async def get_cart(ctx: Context) -> dict[str, Any]:
    """Get the list of items in the cart from Sephora"""
    return await dpage_mcp_tool("https://www.sephora.com/cart/", "sephora_cart")
