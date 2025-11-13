from typing import Any

from fastmcp import Context

from getgather.mcp.registry import GatherMCP
from getgather.zen_distill import short_lived_mcp_tool

cnn_mcp = GatherMCP(brand_id="cnn", name="CNN MCP")


@cnn_mcp.tool
async def get_latest_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest stories from CNN."""
    terminated, result = await short_lived_mcp_tool(
        location="https://lite.cnn.com",
        pattern_wildcard="**/cnn-*.html",
        result_key="stories",
        url_hostname="cnn.com",
    )
    if not terminated:
        raise ValueError("Failed to retrieve CNN stories")
    return result
