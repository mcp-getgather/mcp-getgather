from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

petsmart_mcp = GatherMCP(brand_id="petsmart", name="Petsmart MCP")


@petsmart_mcp.tool
async def get_cart(ctx: Context) -> dict[str, Any]:
    """Get the list of items in the cart from Petsmart"""
    return await dpage_mcp_tool("https://www.petsmart.com/cart/", "petsmart_cart")
