from typing import Any

from fastmcp import Context

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract

zillow_mcp = BrandMCPBase(prefix="zillow", name="Zillow MCP")


@zillow_mcp.tool(tags={"private"})
async def get_favorites(
    ctx: Context,
) -> dict[str, Any]:
    """Get favorites of zillow."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("zillow"))
