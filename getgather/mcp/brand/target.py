from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

target_mcp = BrandMCPBase(brand_id="target", name="Target MCP")


@target_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get items purchased from Target."""
    return await extract()
