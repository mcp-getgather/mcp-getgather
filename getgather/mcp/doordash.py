import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import GatherMCP

doordash_mcp = GatherMCP(brand_id="doordash", name="Doordash MCP")


# TODO: add signin pattern
async def get_orders() -> dict[str, Any]:
    """Get orders from Doordash.com."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    _terminated, distilled, converted = await run_distillation_loop(
        "https://www.doordash.com/orders", patterns
    )
    orders = converted if converted else distilled
    return {"orders": orders}
