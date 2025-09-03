from typing import Any

from fastmcp import Context

from getgather.mcp.agent import run_agent_for_brand
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract
from getgather.mcp.stagehand_agent import (
    run_stagehand_agent,
)

goodreads_mcp = BrandMCPBase(brand_id="goodreads", name="Goodreads MCP")


@goodreads_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get the book list from a user's Goodreads account."""
    return await extract()


@goodreads_mcp.tool(tags={"private"})
async def get_book_list_stagehand() -> dict[str, Any]:
    """Get the book list from a user's Goodreads account using Stagehand agent."""

    page = await run_stagehand_agent()
    await page.goto("https://www.goodreads.com")
    await page.act("Navigate to My Books")
    books = await page.extract("Extract all book titles and authors")

    return books


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
