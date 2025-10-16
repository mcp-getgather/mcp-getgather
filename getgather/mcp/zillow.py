from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

zillow_mcp = GatherMCP(brand_id="zillow", name="Zillow MCP")


@zillow_mcp.tool
async def get_favorites() -> dict[str, Any]:
    """Get favorites of zillow."""
    return await dpage_mcp_tool("https://www.zillow.com/myzillow/favorites", "zillow_favorites")
