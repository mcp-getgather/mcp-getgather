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

    final_purchase_history: list[dict[str, Any]] = []

    if purchase_history and isinstance(purchase_history, list) and len(purchase_history) > 0:
        for i in range(len(purchase_history)):
            purchase = purchase_history[i]
            order_date_and_store = str(purchase["order_date_and_store"])
            # NOTE: sometimes the order_id is not returned, so we need to use the order_date_and_store to get the order_id
            order_id = order_date_and_store.split("#")[1]

            invoice_history = await run_distillation_loop(
                f"https://www.wayfair.com/v/account/order/details?order_id={order_id}",
                patterns,
                browser_profile=browser_profile,
            )

            if invoice_history and isinstance(invoice_history, list) and len(invoice_history) > 0:
                final_purchase_history.append({
                    "order_id": order_id,
                    "order_date_and_store": order_date_and_store,
                    "total_price": purchase["total_price"],
                    "total_item": purchase["total_item"],
                    "delivery_date": purchase["delivery_date"],
                    "details": invoice_history,
                })
            else:
                final_purchase_history.append({
                    "order_id": order_id,
                    "order_date_and_store": order_date_and_store,
                    "total_price": purchase["total_price"],
                    "total_item": purchase["total_item"],
                    "delivery_date": purchase["delivery_date"],
                    "details": [],
                })

    return {"purchase_history": final_purchase_history}
