from typing import Any

from fastmcp import Context, FastMCP

from getgather.mcp.dpage import dpage_mcp_tool

bbc_mcp = FastMCP[Context](name="BBC MCP")


@bbc_mcp.tool
async def get_saved_articles(ctx: Context) -> dict[str, Any]:
    """Get the list of saved articles from BBC news site"""

    return await dpage_mcp_tool("https://www.bbc.com/saved", "saved_articles")
