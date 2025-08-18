from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

gofood_mcp = BrandMCPBase(brand_id="gofood", name="Gofood MCP")


@gofood_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get gofood purchase history."""
    return await extract()
