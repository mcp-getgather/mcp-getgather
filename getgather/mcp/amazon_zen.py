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
