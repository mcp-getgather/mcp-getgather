import os
from typing import Any

from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session

kindle_mcp = BrandMCPBase(brand_id="kindle", name="Kindle MCP")


@kindle_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_book_list(*, browser_session: BrowserSession | None = None) -> dict[str, Any]:
    """Get book list from Amazon Kindle."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    books = await run_distillation_loop(
        "https://www.amazon.com/hz/mycd/digital-console/contentlist/booksAll/dateDsc/",
        patterns,
        browser_session=browser_session,
    )
    return {"books": books}
