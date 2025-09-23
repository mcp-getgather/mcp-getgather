from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

espn_mcp = GatherMCP(brand_id="espn", name="ESPN MCP")


@espn_mcp.tool
async def get_schedule(ctx: Context) -> dict[str, Any]:
    """Get the week's college football schedule from ESPN."""
    return await dpage_mcp_tool(
        "https://www.espn.com/college-football/schedule", "college_football_schedule"
    )
