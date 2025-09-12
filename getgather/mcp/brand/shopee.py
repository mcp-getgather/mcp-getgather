import os
from typing import Any
from urllib.parse import quote

from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.profile_manager import global_profile_manager
from getgather.mcp.shared import (
    get_global_browser_session,
    with_global_browser_session,
)
from getgather.parse import parse_html

shopee_mcp = BrandMCPBase(brand_id="shopee", name="Shopee MCP")


@shopee_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase history of a shopee."""
    browser_profile = global_profile_manager.get_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    purchase_history = await run_distillation_loop(
        "https://shopee.co.id/user/purchase", patterns, browser_profile=browser_profile
    )
    return {"purchase_history": purchase_history}


@shopee_mcp.tool
@with_global_browser_session
async def search_product(keyword: str, page_number: int = 1) -> dict[str, Any]:
    """Search product on shopee."""
    browser_session = get_global_browser_session()
    page = await browser_session.page()

    # URL encode the search keyword
    encoded_keyword = quote(keyword)
    await page.goto(
        f"https://shopee.co.id/search?keyword={encoded_keyword}&page={page_number - 1}",
        wait_until="commit",
    )
    await page.wait_for_selector(
        "ul.shopee-search-item-result__items > li:nth-child(1) > div:nth-child(1)"
    )
    await page.wait_for_timeout(1000)
    html = await page.locator("section.shopee-search-item-result").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "li.shopee-search-item-result__item",
        "columns": [
            {
                "name": "product_name",
                "selector": "a[class='contents'] > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(1)",
            },
            {"name": "product_url", "selector": "a[class='contents']", "attribute": "href"},
            {
                "name": "price",
                "selector": "a[class='contents'] > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)",
            },
            {
                "name": "discount_percentage",
                "selector": "a[class='contents'] > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2)",
            },
        ],
    })
    result = await parse_html(brand_id=shopee_mcp.brand_id, html_content=html, schema=spec_schema)
    return {"product_list": result.content}
