from typing import Any

from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

zillow_mcp = BrandMCPBase(brand_id="zillow", name="Zillow MCP")


@zillow_mcp.tool(tags={"private"})
async def get_favorites() -> dict[str, Any]:
    """Get favorites of zillow."""
    return await extract()
