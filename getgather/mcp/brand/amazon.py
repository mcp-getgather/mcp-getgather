from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from patchright.async_api import async_playwright

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session
from getgather.parse import parse_html

amazon_mcp = BrandMCPBase(prefix="amazon", name="Amazon MCP")


@amazon_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase/order history of a amazon."""
    return await extract(brand_id=BrandIdEnum("amazon"))


@amazon_mcp.tool
async def search_product(
    keyword: str,
) -> dict[str, Any]:
    """Search product on amazon."""
    q = quote_plus(keyword)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"https://www.amazon.com/s?k={q}")
        # Let the page settle a bit to reduce DOM mutations
        await page.wait_for_load_state("domcontentloaded")
        # Wait for any recognizable result container
        await page.wait_for_selector(
            "div.s-main-slot, #search, [data-component-type='s-search-result']"
        )
        # Snapshot container with fallbacks
        if await page.locator("div.s-main-slot").count() > 0:
            container_html = await page.locator("div.s-main-slot").inner_html()
        elif await page.locator("#search").count() > 0:
            container_html = await page.locator("#search").inner_html()
        else:
            container_html = await page.content()

        spec_schema = SpecSchema.model_validate({
            "bundle": "",
            "format": "html",
            "output": "",
            # Only real products with non-empty data-asin (union of common patterns)
            "row_selector": "[data-asin]:not([data-asin='']), .sg-col[data-asin]:not([data-asin='']), li[data-asin]:not([data-asin=''])",
            "columns": [
                # Product title text
                {
                    "name": "product_name",
                    "selector": "h2 a.a-link-normal[href] span, span.a-size-medium.a-color-base.a-text-normal",
                },
                # Product link (may be /dp/ or ad click wrapper)
                {
                    "name": "product_url",
                    "selector": "h2 a.a-link-normal[href*='/dp/'], h2 a.a-link-normal[href]",
                    "attribute": "href",
                },
                # Price text (visible formatted price)
                {"name": "price", "selector": ".a-price .a-offscreen, span.a-price-whole"},
                # Rating label or reviews text
                {
                    "name": "reviews",
                    "selector": "[aria-label*='out of 5 stars'], .a-size-base.s-underline-text",
                },
            ],
        })

        # Parse from the snapshot; also dump full HTML for debugging
        result = await parse_html(
            schema=spec_schema,
            html_content=container_html,
            dump_html_path=Path("data/debug/amazon_search.html"),
        )
        # Normalize URLs to absolute
        # Type-safe normalization of URLs
        from typing import Any, cast

        rows_typed = cast(list[dict[str, Any]], result.content)
        for row in rows_typed:
            url_val = row.get("product_url")
            if isinstance(url_val, str) and url_val.startswith("/"):
                row["product_url"] = f"https://www.amazon.com{url_val}"
        await browser.close()
    return {"product_list": result.content}


@amazon_mcp.tool
async def get_product_detail(
    product_url: str,
) -> dict[str, Any]:
    """Get product detail from amazon."""
    if BrandState.is_brand_connected(BrandIdEnum("amazon")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("amazon"))
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
    browser_session = await start_browser_session(brand_id=BrandIdEnum("amazon"))
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/cart/view.html")
    await page.wait_for_selector("div#sc-active-cart")
    await page.wait_for_timeout(1000)
    html = await page.locator("div#sc-active-cart").inner_html()
    return {"cart_summary_html": html}


@amazon_mcp.tool(tags={"private"})
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("amazon"))
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/history?ref_=nav_AccountFlyout_browsinghistory")
    await page.wait_for_timeout(1000)
    await page.wait_for_selector("div[class*='desktop-grid']")
    html = await page.locator("div[class*='desktop-grid']").inner_html()
    return {"browsing_history_html": html}
