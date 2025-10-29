from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

shopee_mcp = GatherMCP(brand_id="shopee", name="Shopee MCP")


@shopee_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase history of a shopee."""
    return await dpage_mcp_tool("https://shopee.co.id/user/purchase", "shopee_purchase_history")
