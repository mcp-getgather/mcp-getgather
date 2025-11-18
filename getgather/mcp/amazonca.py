import asyncio
import json
import os
from datetime import datetime
from typing import Any, cast

from patchright.async_api import Page, Response

from getgather.browser.profile import BrowserProfile
from getgather.distill import convert, load_distillation_patterns, run_distillation_loop
from getgather.logs import logger
from getgather.mcp.dpage import dpage_mcp_tool, dpage_with_action
from getgather.mcp.registry import GatherMCP

amazonca_mcp = GatherMCP(brand_id="amazonca", name="Amazon CA MCP")


@amazonca_mcp.tool
async def dpage_get_purchase_history(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon canada."""

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
        f"https://www.amazon.ca/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        "amazonca_purchase_history",
    )


@amazonca_mcp.tool
async def dpage_get_purchase_history_with_details(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon canada with details (product prices)."""

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

    async def get_order_details_action(
        page: Page, browser_profile: BrowserProfile
    ) -> dict[str, Any]:
        current_url = page.url
        if "signin" in current_url:
            raise Exception("User is not signed in")

        path = os.path.join(os.path.dirname(__file__), "patterns", "**/amazon-*.html")

        logger.info(f"Loading patterns from {path}")
        patterns = load_distillation_patterns(path)
        logger.info(f"Loaded {len(patterns)} patterns")
        _, _, orders = await run_distillation_loop(
            f"https://www.amazon.ca/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
            patterns,
            browser_profile=browser_profile,
            interactive=False,
            timeout=2,
            stop_ok=False,
        )
        if orders is None:
            return {"amazon_purchase_history": []}

        async def get_order_details(order_id: str):
            url = f"https://www.amazon.ca/gp/css/summary/print.html?orderID={order_id}&ref=ppx_yo2ov_dt_b_fed_invoice_pos"
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
                get_order_details(order["order_id"])  # pyright: ignore[reportArgumentType]
                for order in orders
            ])
            order_prices = {item["order_id"]: item["prices"] for item in order_prices_list}
            for order in orders:
                if order_prices[order["order_id"]] is not None:
                    order["product_prices"] = order_prices[order["order_id"]]
        except Exception:
            logger.error(f"Error getting order details for order")
            pass
        return {"amazonca_purchase_history": orders}

    return await dpage_with_action(
        f"https://www.amazonca.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        action=get_order_details_action,
    )


@amazonca_mcp.tool
async def dpage_search_purchase_history(keyword: str, page_number: int = 1) -> dict[str, Any]:
    """Search purchase history from amazon ca."""
    return await dpage_mcp_tool(
        f"https://www.amazon.ca/your-orders/search?page={page_number}&search={keyword}",
        "order_history",
    )


@amazonca_mcp.tool
async def search_product(keyword: str) -> dict[str, Any]:
    """Search product on amazon ca."""
    return await dpage_mcp_tool(
        f"https://www.amazon.ca/s?k={keyword}",
        "product_list",
    )


@amazonca_mcp.tool
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon canada."""

    async def get_browsing_history_action(
        page: Page, browser_profile: BrowserProfile
    ) -> dict[str, Any]:
        current_url = page.url
        if "signin" in current_url:
            raise Exception("User is not signed in")

        def _url_matches(resp: Response) -> bool:
            """Predicate that checks if the response URL contains the predicate string."""

            return "browsing-history/" in resp.url

        response: Response = cast(
            Response,
            await page.wait_for_event(  # type: ignore[reportUnknownReturnType]
                "response",
                _url_matches,
                timeout=90_000,
            ),
        )

        browsing_history_url = response.url

        raw_attribute = await page.locator("div[data-client-recs-list]").get_attribute(
            "data-client-recs-list"
        )
        output = [json.dumps(item) for item in json.loads(raw_attribute or "[]")]

        async def get_browsing_history(start_index: int, end_index: int):
            logger.info(f"Getting browsing history from {start_index} to {end_index}")
            re = await page.request.post(
                url=browsing_history_url,
                data=json.dumps({"ids": output[start_index:end_index]}),
                headers=response.request.headers,
            )
            html = await re.text()
            distilled = f"""
                <html gg-domain="amazon">
                    <body>
                        {html}
                    </body>
                    <script type="application/json" id="browsing_history">
                        {{
                            "rows": "div#gridItemRoot",
                            "columns": [
                                {{
                                    "name": "name",
                                    "selector": "a.a-link-normal > span > div"
                                }},
                                {{
                                    "name": "url",
                                    "selector": "div[class*='uncoverable-faceout'] > a[class='a-link-normal aok-block']",
                                    "attribute": "href"
                                }},
                                {{
                                    "name": "image_url",
                                    "selector": "a > div > img.a-dynamic-image",
                                    "attribute": "src"
                                }},
                                {{
                                    "name": "rating",
                                    "selector": "div.a-icon-row > a > i > span"
                                }},
                                {{
                                    "name": "rating_count",
                                    "selector": "div.a-icon-row > a > span"
                                }},
                                {{
                                    "name": "price",
                                    "selector": "span.a-color-price > span"
                                }},
                                {{
                                    "name": "price_unit",
                                    "selector": "span[class='a-size-mini a-color-price aok-nowrap']"
                                }},
                                {{
                                    "name": "delivery_message",
                                    "selector": "div.udm-primary-delivery-message"
                                }}
                            ]
                        }}
                    </script>
                </html>
            """
            return await convert(distilled)

        browsing_history_list = await asyncio.gather(*[
            get_browsing_history(i, i + 100) for i in range(0, len(output), 100)
        ])

        return {"browsing_history_data": browsing_history_list}

    return await dpage_with_action(
        "https://www.amazon.ca/gp/history?ref_=nav_AccountFlyout_browsinghistory",
        action=get_browsing_history_action,
    )
