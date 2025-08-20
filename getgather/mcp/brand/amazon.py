from typing import Any

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session
from getgather.parse import parse_html

amazon_mcp = BrandMCPBase(brand_id="amazon", name="Amazon MCP")


@amazon_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase/order history of a amazon."""
    return await extract(brand_id=amazon_mcp.brand_id)


@amazon_mcp.tool
async def search_product(
    keyword: str,
) -> dict[str, Any]:
    """Search product on amazon."""
    if BrandState.is_brand_connected(amazon_mcp.brand_id):
        profile_id = BrandState.get_browser_profile_id(amazon_mcp.brand_id)
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto(f"https://www.amazon.com/s?k={keyword}")
        await page.wait_for_selector("div[role='listitem]")
        await page.wait_for_timeout(1000)
        html = await page.locator("div.s-search-results").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div[role='listitem']",
        "columns": [
            {"name": "product_name", "selector": "div[data-cy='title-recipe'] > a"},
            {
                "name": "product_url",
                "selector": "div[data-cy='title-recipe'] > a",
                "attribute": "href",
            },
            {"name": "price", "selector": "div[data-cy='price-recipe']"},
            {"name": "reviews", "selector": "div[data-cy='reviews-block']"},
        ],
    })
    result = await parse_html(brand_id=amazon_mcp.brand_id, html_content=html, schema=spec_schema)
    return {"product_list": result.content}


@amazon_mcp.tool
async def get_product_detail(
    product_url: str,
) -> dict[str, Any]:
    """Get product detail from amazon."""
    if BrandState.is_brand_connected(amazon_mcp.brand_id):
        profile_id = BrandState.get_browser_profile_id(amazon_mcp.brand_id)
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        if not product_url.startswith("https"):
            product_url = f"https://www.amazon.com/{product_url}"
        await page.goto(product_url)

        await page.wait_for_selector("span#productTitle")
        await page.wait_for_timeout(1000)
        html = await page.locator("#centerCol").inner_html()
    return {"product_detail_html": html}


@amazon_mcp.tool(tags={"private"})
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from amazon."""
    browser_session = await start_browser_session(brand_id=amazon_mcp.brand_id)
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/cart/view.html")
    await page.wait_for_selector("div#sc-active-cart")
    await page.wait_for_timeout(1000)
    html = await page.locator("div#sc-active-cart").inner_html()
    return {"cart_summary_html": html}


@amazon_mcp.tool(tags={"private"})
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon."""
    browser_session = await start_browser_session(brand_id=amazon_mcp.brand_id)
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/history?ref_=nav_AccountFlyout_browsinghistory")
    await page.wait_for_timeout(1000)
    await page.wait_for_selector("div[class*='desktop-grid']")
    html = await page.locator("div[class*='desktop-grid']").inner_html()
    return {"browsing_history_html": html}
