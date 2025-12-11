from typing import Any

from getgather.mcp.dpage import zen_dpage_mcp_tool
from getgather.mcp.registry import GatherMCP

amain_mcp = GatherMCP(brand_id="amain", name="Amain MCP")


@amain_mcp.tool
async def get_cart() -> dict[str, Any]:
    """Get cart of amain."""
    return await zen_dpage_mcp_tool("https://www.amainhobbies.com/shopping-cart", "amain_cart")
