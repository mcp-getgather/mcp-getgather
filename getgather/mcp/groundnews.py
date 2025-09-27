from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

groundnews_mcp = GatherMCP(brand_id="groundnews", name="Ground News MCP")


@groundnews_mcp.tool
async def get_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest news stories from Ground News."""
    return await dpage_mcp_tool("https://ground.news", "stories", timeout=10)
