from typing import Any
from urllib.parse import urlparse, urlunparse

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

cnn_mcp = GatherMCP(brand_id="cnn", name="CNN MCP")


@cnn_mcp.tool
async def get_latest_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest stories from CNN."""
    result = await dpage_mcp_tool("https://lite.cnn.com", "stories")
    if "stories" in result:
        for story in result["stories"]:
            link: str = story["link"]
            parsed = urlparse(link)
            netloc: str = parsed.netloc if parsed.netloc else "cnn.com"
            url: str = urlunparse((
                "https",
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ))
            story["url"] = url

    return result
