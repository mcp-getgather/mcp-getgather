from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

starbucks_mcp = GatherMCP(brand_id="starbucks", name="Starbucks MCP")


@starbucks_mcp.tool
async def get_my_rewards() -> dict[str, Any]:
    """Get my rewards of Starbucks."""
    return await dpage_mcp_tool("https://www.starbucks.com/account/rewards", "starbucks_my_rewards")
