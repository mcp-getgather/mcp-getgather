from typing import Any

from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

officedepot_mcp = GatherMCP(brand_id="officedepot", name="Office Depot MCP")


@officedepot_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get the purchase history from a user's account."""
    return await dpage_mcp_tool(
        "https://www.officedepot.com/orderhistory/orderHistoryListSet.do?ordersInMonths=0&orderType=ALL&orderStatus=A&searchValue=",
        "officedepot_purchase_history",
    )
