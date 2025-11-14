from typing import Any

from fastmcp import Context

from getgather.mcp.registry import GatherMCP
from getgather.zen_distill import short_lived_mcp_tool

groundnews_mcp = GatherMCP(brand_id="groundnews", name="Ground News MCP")


@groundnews_mcp.tool
async def get_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest news stories from Ground News."""
    terminated, result = await short_lived_mcp_tool(
        location="https://ground.news",
        pattern_wildcard="**/groundnews-*.html",
        result_key="stories",
        url_hostname="ground.news",
    )
    if not terminated:
        raise ValueError("Failed to retrieve Ground News stories")
    return result
