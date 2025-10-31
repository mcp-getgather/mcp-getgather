import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

wayfair_mcp = BrandMCPBase(brand_id="wayfair", name="Wayfair MCP")


@wayfair_mcp.tool(tags={"private"})
async def get_order_history_details(order_id: str) -> dict[str, Any]:
    """Get order history details for a specific Wayfair order."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    _terminated, distilled, converted = await run_distillation_loop(
        f"https://www.wayfair.com/v/account/order/details?order_id={order_id}",
        patterns,
        browser_profile=browser_profile,
    )
    purchase_history_details = converted if converted else distilled

    # Edit image URLs to use higher resolution
    if purchase_history_details and isinstance(purchase_history_details, list):
        for item in purchase_history_details:
            item["order_id"] = order_id
            if "image_url" in item:
                image_url = item["image_url"]
                if isinstance(image_url, str):
                    # Replace dimensions to get higher resolution images
                    image_url = image_url.replace("-h100", "-h500")
                    image_url = image_url.replace("-w100", "-w500")
                    item["image_url"] = image_url

    return {"purchase_history_details": purchase_history_details}
