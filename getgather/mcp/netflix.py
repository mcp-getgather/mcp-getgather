from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

netflix_mcp = GatherMCP(brand_id="netflix", name="Netflix MCP")


@netflix_mcp.tool
async def get_viewing_activity() -> dict[str, Any]:
    """Get viewing activity of Netflix."""
    return await dpage_mcp_tool(
        "https://www.netflix.com/viewingactivity", "netflix_viewing_activity"
    )
