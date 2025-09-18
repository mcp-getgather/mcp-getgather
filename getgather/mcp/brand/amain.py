import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

amain_mcp = BrandMCPBase(brand_id="amain", name="Amain MCP")


@amain_mcp.tool(tags={"private"})
async def get_cart() -> dict[str, Any]:
    """Get cart of amain."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    cart = await run_distillation_loop(
        "https://www.amainhobbies.com/shopping-cart",
        patterns,
        browser_profile=browser_profile,
    )
    return {"cart": cart}
