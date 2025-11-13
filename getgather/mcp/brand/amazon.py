import os
from datetime import datetime
from typing import Any

from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import (
    get_mcp_browser_profile,
    get_mcp_browser_session,
    with_brand_browser_session,
)
from getgather.parse import parse_html

amazon_mcp = BrandMCPBase(brand_id="amazon", name="Amazon MCP")


@amazon_mcp.tool(tags={"private"})
async def get_purchase_history(
    year: str | int | None = None, start_index: int = 0
) -> dict[str, Any]:
    """Get purchase/order history of a amazon."""

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

    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    _terminated, distilled, converted = await run_distillation_loop(
        f"https://www.amazon.com/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        patterns,
        browser_profile=browser_profile,
        stop_ok=True,
    )
    purchases = converted if converted else distilled
    return {"purchases": purchases}


@amazon_mcp.tool(tags={"private"})
@with_brand_browser_session
async def search_purchase_history(keyword: str) -> dict[str, Any]:
    """Search purchase history of a amazon."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto(
        f"https://www.amazon.com/your-orders/search/ref=ppx_yo2ov_dt_b_search?opt=ab&search={keyword}"
    )
    await page.wait_for_selector("div.a-section.a-spacing-none.a-padding-small")
    await page.wait_for_timeout(1000)
    html = await page.locator("div.a-section.a-spacing-none.a-padding-small").inner_html()

    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.a-section.a-spacing-large.a-spacing-top-large",
        "extraction_method": "python_parser",
        "columns": [
            {
                "name": "product_name",
                "selector": "a.a-link-normal p",
            },
            {
                "name": "product_url",
                "selector": "a.a-link-normal[href*='/dp/']",
                "attribute": "href",
            },
            {"name": "product_image", "selector": "img", "attribute": "src"},
            {
                "name": "order_date",
                "selector": "div.a-row.a-spacing-small > span",
            },
        ],
    })

    result = await parse_html(brand_id=amazon_mcp.brand_id, html_content=html, schema=spec_schema)
    return {"order_history": result.content}
