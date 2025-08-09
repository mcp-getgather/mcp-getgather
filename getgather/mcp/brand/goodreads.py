from typing import Any

from fastmcp import Context

from getgather.browser.agent import run_agent
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session

goodreads_mcp = BrandMCPBase(prefix="goodreads", name="Goodreads MCP")


@goodreads_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get the book list from a user's Goodreads account."""
    return await extract(brand_id=BrandIdEnum("goodreads"))


@goodreads_mcp.tool(tags={"private"})
async def add_book_to_want_to_read(ctx: Context, book_name: str) -> dict[str, Any]:
    """Add a book to the 'Want to Read' list on Goodreads."""
    browser_session = None
    try:
        browser_session = await start_browser_session(BrandIdEnum("goodreads"))
        task = f"Add {book_name} to my Goodreads 'Want to Read' list"
        logger.info(f"Running agent with task: {task}")
        await run_agent(ctx, browser_session.context, task)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error adding book to 'Want to Read' list: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if browser_session:
            await browser_session.stop()


@goodreads_mcp.tool(tags={"private"})
async def get_recommendation(ctx: Context) -> dict[str, Any]:
    """Get recommendation of a goodreads."""
    browser_session = None
    try:
        browser_session = await start_browser_session(BrandIdEnum("goodreads"))
        task = "Get recommendation of a goodreads"
        logger.info(f"Running agent with task: {task}")
        result = await run_agent(ctx, browser_session.context, task)
        return {"status": "success", "result": result.final_result()}
    except Exception as e:
        logger.error(f"Error getting recommendation: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if browser_session:
            await browser_session.stop()
