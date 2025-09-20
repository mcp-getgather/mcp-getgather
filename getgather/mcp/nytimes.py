from typing import Any

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

nytimes_mcp = GatherMCP(brand_id="nytimes", name="NYTimes MCP")


@nytimes_mcp.tool
async def get_bestsellers_list(ctx: Context) -> dict[str, Any]:
    """Get the bestsellers list from NY Times."""
    return await dpage_mcp_tool("https://www.nytimes.com/books/best-sellers/", "best_sellers")
