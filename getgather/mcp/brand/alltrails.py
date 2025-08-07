from typing import Any

from fastmcp import Context

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

alltrails_mcp = BrandMCPBase(prefix="alltrails", name="Alltrails MCP")


@alltrails_mcp.tool(tags={"private"})
async def get_feed(
    ctx: Context,
) -> dict[str, Any]:
    """Get feed of alltrails."""
    return await extract(brand_id=BrandIdEnum("alltrails"))
