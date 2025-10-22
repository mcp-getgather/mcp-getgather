from typing import Any

from fastmcp import Context
from patchright.async_api import Page

from getgather.mcp.agent import run_agent_for_brand
from getgather.mcp.dpage import dpage_callback_tool, dpage_mcp_tool
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.stagehand_agent import (
    run_stagehand_agent,
)

goodreads_mcp = BrandMCPBase(brand_id="goodreads", name="Goodreads MCP")


@goodreads_mcp.tool
async def get_url() -> dict[str, Any]:
    async def callback(page: Page) -> dict[str, Any]:
        await page.click("a:has-text('My Books')")
        return {"url": page.url}

    return await dpage_callback_tool(
        "https://www.goodreads.com/recommendations",
        callback=callback,
    )


@goodreads_mcp.tool
async def get_book_list() -> dict[str, Any]:
    """Get the book list from a user's Goodreads account."""
    return await dpage_mcp_tool(
        "https://www.goodreads.com/review/list?ref=nav_mybooks&view=table",
        "books",
    )


@goodreads_mcp.tool(tags={"private"})
async def get_book_recommendation() -> dict[str, Any]:
    """Get a book recommendation from a user's Goodreads account."""
    stagehand = await run_stagehand_agent()
    await stagehand.page.goto("https://www.goodreads.com/recommendations")
    extract_result = await stagehand.page.extract("Extract all book titles and authors")
    await stagehand.close()
    return {"books": extract_result.model_dump()}


@goodreads_mcp.tool(tags={"private"})
async def add_book_to_want_to_read(ctx: Context, book_name: str) -> dict[str, Any]:
    """Add a book to the 'Want to Read' list on Goodreads."""
    task = (
        f"You are already logged in Goodreads. Find {book_name} and add it to 'Want to Read' list."
    )
    return await run_agent_for_brand(task)


@goodreads_mcp.tool(tags={"private"})
async def get_recommendation(ctx: Context) -> dict[str, Any]:
    """Get recommendation of a goodreads."""
    task = "Get recommendation of a goodreads"
    return await run_agent_for_brand(task)
