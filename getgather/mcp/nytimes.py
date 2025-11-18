from typing import Any

from fastmcp import Context

from getgather.mcp.registry import GatherMCP
from getgather.zen_distill import short_lived_mcp_tool

nytimes_mcp = GatherMCP(brand_id="nytimes", name="NYTimes MCP")


@nytimes_mcp.tool
async def get_bestsellers_list(ctx: Context) -> dict[str, Any]:
    """Get the bestsellers list from NY Times."""
    terminated, result = await short_lived_mcp_tool(
        location="https://www.nytimes.com/books/best-sellers/",
        pattern_wildcard="**/nytimes-*.html",
        result_key="best_sellers",
        url_hostname="nytimes.com",
    )
    if not terminated:
        raise ValueError("Failed to retrieve NY Times best sellers")
    return result
