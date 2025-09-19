import os
from typing import Any

from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_mcp_browser_profile

wayfair_mcp = BrandMCPBase(brand_id="wayfair", name="Wayfair MCP")


@wayfair_mcp.tool(tags={"private"})
async def get_order_history() -> dict[str, Any]:
    """Get order history of wayfair."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    purchase_history = await run_distillation_loop(
        "https://www.wayfair.com/session/secure/account/order_search.php",
        patterns,
        browser_profile=browser_profile,
    )

    if purchase_history and isinstance(purchase_history, list) and len(purchase_history) > 0:
        # Add order_id to each purchase by extracting from order_date_and_store
        for purchase in purchase_history:
            order_date_and_store = str(purchase["order_date_and_store"])
            # NOTE: sometimes the order_id is not returned, so we need to use the order_date_and_store to get the order_id
            order_id = order_date_and_store.split("#")[1]
            purchase["order_id"] = order_id

    return {"purchase_history": purchase_history}
    # return {"purchase_history":[{"order_id":"4325262636","order_date_and_store":"Ordered On: June 4, 2025Wayfair Order #4325262636","total_price":"Total Price: $96.23","total_item":"(2 items)","delivery_date":"Last Package Delivered: Saturday, June 07","product_names":"18 Pack Acoustic Wall Panels 11.8 x 11.8 x 0.4 inch Self-Adhesive Black (Set of 18)","image_urls":"https://assets.wfcdn.com/im/39604481/resize-h85-w85%5Ecompr-r85/3426/342697647/default_name.jpg"}]}


@wayfair_mcp.tool(tags={"private"})
async def get_order_history_details(order_id: str) -> dict[str, Any]:
    """Get order history details for a specific Wayfair order."""
    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    purchase_history_details = await run_distillation_loop(
        f"https://www.wayfair.com/v/account/order/details?order_id={order_id}",
        patterns,
        browser_profile=browser_profile,
    )

    # Edit image URLs to use higher resolution
    if purchase_history_details and isinstance(purchase_history_details, list):
        for item in purchase_history_details:
            if "image_url" in item:
                image_url = item["image_url"]
                if isinstance(image_url, str):
                    # Replace dimensions to get higher resolution images
                    image_url = image_url.replace("-h100", "-h500")
                    image_url = image_url.replace("-w100", "-w500")
                    item["image_url"] = image_url

    return {"purchase_history_details": purchase_history_details}
