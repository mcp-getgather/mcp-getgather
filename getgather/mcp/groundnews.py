from typing import Any
from urllib.parse import urlparse, urlunparse

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

groundnews_mcp = GatherMCP(brand_id="groundnews", name="Ground News MCP")


@groundnews_mcp.tool
async def get_stories(ctx: Context) -> dict[str, Any]:
    """Get the latest news stories from Ground News."""
    result = await dpage_mcp_tool("https://ground.news", "stories", timeout=10)
    if "stories" in result:
        for story in result["stories"]:
            link: str = story["link"]
            parsed = urlparse(link)
            netloc: str = parsed.netloc if parsed.netloc else "ground.news"
            url: str = urlunparse((
                "https",
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ))
            story["url"] = url
    print("STORIES", result)
    return result
