from typing import Any

from patchright.async_api import Page

from getgather.actions import handle_network_extraction
from getgather.mcp.dpage import dpage_with_action
from getgather.mcp.registry import GatherMCP

americanairlines_mcp = GatherMCP(brand_id="americanairlines", name="American Airlines MCP")


@americanairlines_mcp.tool
async def get_upcoming_flights() -> dict[str, Any]:
    """Get upcoming flights of americanairlines."""

    async def action(page: Page) -> dict[str, Any]:
        data = await handle_network_extraction(page, "loyalty/api/upcoming-trips")
        return {"americanairlines_upcoming_flights": data}

    return await dpage_with_action(
        "https://www.aa.com/aadvantage-program/profile/account-summary",
        action,
    )


@americanairlines_mcp.tool
async def get_recent_activity() -> dict[str, Any]:
    """Get recent activity (purchase history) of americanairlines."""

    async def action(page: Page) -> dict[str, Any]:
        data = await handle_network_extraction(
            page, "api/loyalty/miles/transaction/orchestrator/memberActivity"
        )

        return {"americanairlines_recent_activity": data}

    return await dpage_with_action(
        "https://www.aa.com/aadvantage-program/profile/account-summary",
        action,
    )
