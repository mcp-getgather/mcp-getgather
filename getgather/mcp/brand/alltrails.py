from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

alltrails_mcp = BrandMCPBase(brand_id="alltrails", name="Alltrails MCP")


@alltrails_mcp.tool(tags={"private"})
async def get_feed() -> dict[str, Any]:
    """Get feed of alltrails."""
    return await extract()
