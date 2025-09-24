from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

npr_mcp = GatherMCP(brand_id="npr", name="NPR MCP")


@npr_mcp.tool
async def get_headlines(ctx: Context) -> dict[str, Any]:
    """Get the current news headlines from NPR."""
    return await dpage_mcp_tool("https://text.npr.org", "headlines")
