from datetime import datetime
from typing import Any

from getgather.mcp.dpage import zen_dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

amazon_zen_mcp = GatherMCP(brand_id="amazon_zen", name="Amazon Zen MCP")


@amazon_zen_mcp.tool
async def search_purchase_history(keyword: str, page_number: int = 1) -> dict[str, Any]:
    """Search purchase history from amazon."""
    return await zen_dpage_mcp_tool(
        f"https://www.amazon.com/your-orders/search?page={page_number}&search={keyword}",
        "order_history",
    )


@amazon_zen_mcp.tool
async def get_purchase_history(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon with dpage."""

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

    return await zen_dpage_mcp_tool(
        f"https://www.amazon.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        "amazon_purchase_history",
    )


@amazon_zen_mcp.tool
async def search_product(keyword: str) -> dict[str, Any]:
    """Search product on amazon."""
    return await zen_dpage_mcp_tool(
        f"https://www.amazon.com/s?k={keyword}",
        "product_list",
    )
