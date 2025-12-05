from typing import Any

import zendriver as zd

from getgather.mcp.dpage import zen_dpage_mcp_tool, zen_dpage_with_action
from getgather.mcp.registry import GatherMCP

goodreads_mcp = GatherMCP(brand_id="goodreads", name="Goodreads MCP")


@goodreads_mcp.tool
async def get_web_title() -> dict[str, Any]:
    """Get the web title from a user's Goodreads account."""

    async def action(tab: zd.Tab, _) -> dict[str, Any]:
        # all of the feature of Tab is coming from zen instead of patchright -> so migration is needed
        title = await tab.evaluate("document.title")
        url = tab.url
        return {"web_title": title, "url": url}

    return await zen_dpage_with_action(
        "https://www.goodreads.com/review/list?ref=nav_mybooks&view=table",
        action,
    )


@goodreads_mcp.tool
async def get_book_list() -> dict[str, Any]:
    """Get the book list from a user's Goodreads account."""
    return await zen_dpage_mcp_tool(
        "https://www.goodreads.com/review/list?ref=nav_mybooks&view=table", "goodreads_book_list"
    )
