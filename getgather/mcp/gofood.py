from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

gofood_mcp = GatherMCP(brand_id="gofood", name="Gofood MCP")


@gofood_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get gofood purchase history."""
    return await dpage_mcp_tool("https://gofood.co.id/en/orders", "gofood_purchase_history")
