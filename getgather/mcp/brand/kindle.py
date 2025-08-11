from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

kindle_mcp = BrandMCPBase(prefix="kindle", name="Kindle MCP")


@kindle_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get book list from Amazon Kindle."""
    return await extract(BrandIdEnum("kindle"))
