from datetime import datetime
from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

amazonca_mcp = GatherMCP(brand_id="amazonca", name="Amazon CA MCP")


@amazonca_mcp.tool
async def dpage_get_purchase_history(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon canada."""

    if year is None:
        target_year = datetime.now().year
    elif isinstance(year, str):
        try:
            target_year = int(year)
        except ValueError:
            target_year = datetime.now().year
    else:
        target_year = int(year)

    current_year = datetime.now().year
    if not (1900 <= target_year <= current_year + 1):
        raise ValueError(f"Year {target_year} is out of valid range (1900-{current_year + 1})")

    return await dpage_mcp_tool(
        f"https://www.amazon.ca/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        "amazonca_purchase_history",
    )


@amazonca_mcp.tool
async def get_purchase_history(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon canada."""

    if year is None:
        target_year = datetime.now().year
    elif isinstance(year, str):
        try:
            target_year = int(year)
        except ValueError:
            target_year = datetime.now().year
    else:
        target_year = int(year)

    current_year = datetime.now().year
    if not (1900 <= target_year <= current_year + 1):
        raise ValueError(f"Year {target_year} is out of valid range (1900-{current_year + 1})")

    return await dpage_mcp_tool(
        f"https://www.amazon.ca/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        "amazonca_purchase_history",
    )


@amazonca_mcp.tool
async def search_purchase_history(keyword: str) -> dict[str, Any]:
    """Search purchase history from amazon ca."""
    return await dpage_mcp_tool(
        f"https://www.amazon.ca/your-orders/search/ref=ppx_yo2ov_dt_b_search?opt=ab&search={keyword}",
        "order_history",
    )


@amazonca_mcp.tool
async def search_product(keyword: str) -> dict[str, Any]:
    """Search product on amazon ca."""
    return await dpage_mcp_tool(
        f"https://www.amazon.ca/s?k={keyword}",
        "product_list",
    )


@amazonca_mcp.tool
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon."""
    return await dpage_mcp_tool(
        "https://www.amazon.ca/gp/history?ref_=nav_AccountFlyout_browsinghistory",
        "browsing_history",
    )
