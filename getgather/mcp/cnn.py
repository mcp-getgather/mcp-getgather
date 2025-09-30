from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

cnn_mcp = GatherMCP(brand_id="cnn", name="CNN MCP")


@cnn_mcp.tool
async def get_latest_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest stories from CNN."""
    return await dpage_mcp_tool("https://lite.cnn.com", "stories")
