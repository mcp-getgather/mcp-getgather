from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

goodreads_mcp = BrandMCPBase(prefix="goodreads", name="Goodreads MCP")


@goodreads_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get the book list from a user's Goodreads account."""
    return await extract(brand_id=BrandIdEnum("goodreads"))
