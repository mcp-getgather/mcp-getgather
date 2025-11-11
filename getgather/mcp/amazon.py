import asyncio
from datetime import datetime
from typing import Any

from patchright.async_api import Page

from getgather.logs import logger
from getgather.mcp.dpage import dpage_mcp_tool, dpage_with_action
from getgather.mcp.registry import GatherMCP

amazon_mcp = GatherMCP(brand_id="amazon", name="Amazon MCP")


@amazon_mcp.tool
async def dpage_get_purchase_history(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon with dpage."""

    if year is None:
        target_year = datetime.now().year
    elif isinstance(year, str):
        try:
            target_year = int(year)
        except ValueError:
            target_year = datetime.now().year
    else:
        target_year = int(year)

    current_year = datetime.now().year
    if not (1900 <= target_year <= current_year + 1):
        raise ValueError(f"Year {target_year} is out of valid range (1900-{current_year + 1})")

    async def get_order_details_action(page: Page) -> dict[str, Any]:
        current_url = page.url
        if "signin" in current_url:
            raise Exception("User is not signed in")

        dpage_result = await dpage_mcp_tool(
            f"https://www.amazon.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
            "amazon_purchase_history",
        )
        orders = dpage_result["amazon_purchase_history"]

        async def get_order_details(order_id: str):
            url = f"https://www.amazon.com/gp/css/summary/print.html?orderID={order_id}&ref=ppx_yo2ov_dt_b_fed_invoice_pos"
            prices = await page.evaluate(f"""
                    async () => {{
                        const res = await fetch('{url}', {{
                            method: 'GET',
                            credentials: 'include',
                        }});
                        const text = await res.text();
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(text, 'text/html');
                        doc.querySelectorAll('script').forEach(s => s.remove());
                        
                        const rows = doc.querySelectorAll("div.a-fixed-left-grid");
                        const prices = Array.from(rows)
                            .map(row => row.querySelector("span.a-price span.a-offscreen")?.textContent?.trim())
                            .filter(Boolean);
                        return prices;
                    }}
                """)
            return {"order_id": order_id, "prices": prices}

        try:
            order_prices_list = await asyncio.gather(*[
                get_order_details(order["order_id"]) for order in orders
            ])
            order_prices = {item["order_id"]: item["prices"] for item in order_prices_list}
            for order in orders:
                if order_prices[order["order_id"]] is not None:
                    order["product_prices"] = order_prices[order["order_id"]]
        except Exception:
            logger.error(f"Error getting order details for order")
            pass
        return {"orders": orders, "current_url": current_url}

    return await dpage_with_action(
        f"https://www.amazon.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        action=get_order_details_action,
    )
