from typing import Any
from urllib.parse import quote

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract
from getgather.mcp.store import BrandConnectionStore
from getgather.parse import parse_html

shopee_mcp = BrandMCPBase(prefix="shopee", name="Shopee MCP")


@shopee_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase history of a shopee."""
    return await extract(brand_id=BrandIdEnum("shopee"))


@shopee_mcp.tool
async def search_product(
    keyword: str,
    page_number: int = 1,
) -> dict[str, Any]:
    """Search product on shopee."""
    if BrandConnectionStore.is_brand_connected(BrandIdEnum("shopee")):
        profile_id = BrandConnectionStore.get_browser_profile_id(BrandIdEnum("shopee"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()

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
    result = await parse_html(brand_id=BrandIdEnum("shopee"), html_content=html, schema=spec_schema)
    return {"product_list": result.content}
