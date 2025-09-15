from typing import Any

from fastmcp import Context, FastMCP

from getgather.mcp.dpage import dpage_mcp_tool

espn_mcp = FastMCP[Context](name="ESPN MCP")


@espn_mcp.tool
async def get_schedule(ctx: Context) -> dict[str, Any]:
    """Get the week's college football schedule from ESPN."""
    return await dpage_mcp_tool(
        "https://www.espn.com/college-football/schedule", "college_football_schedule"
    )
