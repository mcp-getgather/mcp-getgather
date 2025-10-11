import os
from typing import Any

from getgather.browser.session import BrowserSession
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_session, with_brand_browser_session

lululemon_mcp = BrandMCPBase(brand_id="lululemon", name="Lululemon MCP")


@lululemon_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_orders(*, browser_session: BrowserSession | None = None) -> dict[str, Any]:
    """Get orders from Lululemon."""
    browser_session = browser_session or get_mcp_browser_session()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    orders = await run_distillation_loop(
        "https://shop.lululemon.com/account/purchase-history",
        patterns,
        browser_session=browser_session,
    )
    return {"orders": orders}
