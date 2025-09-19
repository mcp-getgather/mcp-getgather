import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

seatgeek_mcp = BrandMCPBase(brand_id="seatgeek", name="SeatGeek MCP")


@seatgeek_mcp.tool(tags={"private"})
async def get_tickets() -> dict[str, Any]:
    """Get tickets of seatgeek."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    tickets = await run_distillation_loop(
        "https://seatgeek.com/account/tickets",
        patterns,
        browser_profile=browser_profile,
    )
    return {"tickets": tickets}
