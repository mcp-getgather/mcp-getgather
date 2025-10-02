from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

cnn_mcp = GatherMCP(brand_id="cnn", name="CNN MCP")


@cnn_mcp.tool
async def get_latest_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest stories from CNN."""
    return await dpage_mcp_tool("https://lite.cnn.com", "stories")


@cnn_mcp.tool
async def get_subscribed_newsletter(ctx: Context) -> dict[str, Any]:
    """Get the subscribed newsletter from CNN."""
    return await dpage_mcp_tool("https://www.cnn.com/newsletters", "cnn_subscribed_newsletter")
