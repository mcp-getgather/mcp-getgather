import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.profile_manager import global_profile_manager

gofood_mcp = BrandMCPBase(brand_id="gofood", name="Gofood MCP")


@gofood_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get gofood purchase history."""
    browser_profile = global_profile_manager.get_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    purchases = await run_distillation_loop(
        "https://gofood.co.id/en/orders", patterns, browser_profile=browser_profile
    )
    return {"purchases": purchases}
