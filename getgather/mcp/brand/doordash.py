from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

doordash_mcp = BrandMCPBase(prefix="doordash", name="Doordash MCP")


@doordash_mcp.tool(tags={"private"})
async def get_orders() -> dict[str, Any]:
    """Get orders from Doordash.com."""
    return await extract(BrandIdEnum("doordash"))
