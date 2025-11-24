from typing import Any

from fastmcp import Context

from getgather.mcp.registry import GatherMCP
from getgather.zen_distill import short_lived_mcp_tool

espn_mcp = GatherMCP(brand_id="espn", name="ESPN MCP")


@espn_mcp.tool
async def get_schedule(ctx: Context) -> dict[str, Any]:
    """Get the week's college football schedule from ESPN."""
    terminated, result = await short_lived_mcp_tool(
        location="https://www.espn.com/college-football/schedule",
        pattern_wildcard="**/espn-*.html",
        result_key="college_football_schedule",
        url_hostname="espn.com",
    )
    if not terminated:
        raise ValueError("Failed to retrieve ESPN college football schedule")
    return result
