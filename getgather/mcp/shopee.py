from typing import Any
from urllib.parse import quote

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.dpage import dpage_mcp_tool
from getgather.mcp.registry import GatherMCP
from getgather.mcp.shared import (
    get_mcp_browser_session,
    with_brand_browser_session,
)
from getgather.parse import parse_html

shopee_mcp = GatherMCP(brand_id="shopee", name="Shopee MCP")


@shopee_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase history of a shopee."""
    return await dpage_mcp_tool("https://shopee.co.id/user/purchase", "shopee_purchase_history")


@shopee_mcp.tool
async def search_product(keyword: str, page_number: int = 1) -> dict[str, Any]:
    """Search product on shopee."""
    url = f"https://shopee.co.id/search?keyword={keyword}"
    return await dpage_mcp_tool(url, "shopee_search_product")
