from fastmcp import Context
from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum


from fastmcp.utilities.logging import get_logger

from getgather.mcp.shared import extract
from getgather.mcp.registry import BrandMCPBase

logger = get_logger(__name__)


alltrails_mcp = BrandMCPBase(prefix="alltrails", name="Alltrails MCP")


@alltrails_mcp.tool(tags={"private"})
async def get_feed(
    ctx: Context,
) -> dict[str, Any]:
    """Get feed of alltrails."""
    return await extract(session_id=ctx.session_id, brand_id=BrandIdEnum("alltrails"))
