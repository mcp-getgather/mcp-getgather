from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

americanairlines_mcp = GatherMCP(brand_id="americanairlines", name="American Airlines MCP")


@americanairlines_mcp.tool
async def get_upcoming_flights() -> dict[str, Any]:
    """Get upcoming flights of americanairlines."""
    return await dpage_mcp_tool(
        "https://www.aa.com/aadvantage-program/profile/account-summary",
        "americanairlines_upcoming_flights",
        timeout=10
    )
