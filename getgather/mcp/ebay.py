from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

ebay_mcp = GatherMCP(brand_id="ebay", name="Ebay MCP")


@ebay_mcp.tool
async def get_cart(ctx: Context) -> dict[str, Any]:
    """Get the list of items in the cart from Ebay"""

    return await dpage_mcp_tool("https://cart.ebay.com/", "ebay_cart")
