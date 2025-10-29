from typing import Any

from fastmcp import Context

from getgather.distill import short_lived_mcp_tool
from getgather.mcp.registry import GatherMCP

npr_mcp = GatherMCP(brand_id="npr", name="NPR MCP")


@npr_mcp.tool
async def get_headlines(ctx: Context) -> dict[str, Any]:
    """Get the current news headlines from NPR."""
    terminated, result = await short_lived_mcp_tool(
        location="https://text.npr.org",
        pattern_wildcard="**/npr-*.html",
        result_key="headlines",
        url_hostname="npr.org",
    )
    if not terminated:
        raise ValueError("Failed to retrieve NPR headlines")
    return result
