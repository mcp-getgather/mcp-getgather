from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

gofood_mcp = BrandMCPBase(prefix="gofood", name="Gofood MCP")


@gofood_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get gofood purchase history."""
    return await extract(brand_id=BrandIdEnum("gofood"))
