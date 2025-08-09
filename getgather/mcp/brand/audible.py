from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

audible_mcp = BrandMCPBase(prefix="audible", name="Audible MCP")


@audible_mcp.tool(tags={"private"})
async def get_book_list() -> dict[str, Any]:
    """Get book list from Audible.com."""
    return await extract(BrandIdEnum("audible"))
