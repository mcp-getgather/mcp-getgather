import asyncio
from datetime import datetime
from typing import Any

from patchright.async_api import Page

from getgather.distill import convert
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

    return await dpage_mcp_tool(
        f"https://www.amazon.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        "amazon_purchase_history",
    )


@amazon_mcp.tool
async def dpage_get_purchase_history_with_details(
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
            html = await page.evaluate(f"""
                    async () => {{
                        const res = await fetch('{url}', {{
                            method: 'GET',
                            credentials: 'include',
                        }});
                        const text = await res.text();
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(text, 'text/html');
                        doc.querySelectorAll('script').forEach(s => s.remove());
                        return doc.body.innerHTML;
                    }}
                """)
            distilled = f"""
                    <html gg-domain="amazon">
                        <body>
                            {html}
                        </body>
                        <script type="application/json" id="orders">
                            {{
                                "rows": "div[class='a-fixed-left-grid']",
                                "columns": [
                                    {{
                                        "name": "price",
                                        "selector": "span.a-price span.a-offscreen"
                                    }}
                                ]
                            }}
                        </script>
                    </html>
                """
            converted = await convert(distilled)
            return {"order_id": order_id, "converted": converted}

        order_details_list = await asyncio.gather(*[
            get_order_details(order["order_id"]) for order in orders
        ])

        order_details = {item["order_id"]: item["converted"] for item in order_details_list}

        for order in orders:
            order_detail = order_details[order["order_id"]]
            if order_detail is not None:
                order["product_prices"] = [
                    item["price"]  # pyright: ignore[reportArgumentType]
                    for item in order_detail
                ]

        return {"orders": orders, "order_details": order_details, "current_url": current_url}

    return await dpage_with_action(
        f"https://www.amazon.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        action=get_order_details_action,
    )
