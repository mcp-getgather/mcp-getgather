from typing import Any
from urllib.parse import urlparse, urlunparse

from fastmcp import Context

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

npr_mcp = GatherMCP(brand_id="npr", name="NPR MCP")


@npr_mcp.tool
async def get_headlines(ctx: Context) -> dict[str, Any]:
    """Get the current news headlines from NPR."""

    result = await dpage_mcp_tool("https://text.npr.org", "headlines")
    if "headlines" in result:
        for headline in result["headlines"]:
            link: str = headline["link"]
            parsed = urlparse(link)
            netloc: str = parsed.netloc if parsed.netloc else "npr.org"
            url: str = urlunparse((
                "https",
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ))
            headline["url"] = url
    return result
