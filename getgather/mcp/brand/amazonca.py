import os
from datetime import datetime
from typing import Any

from fastmcp import Context

from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.distill import load_distillation_patterns, run_distillation_loop
from getgather.mcp.agent import run_agent_for_brand
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import (
    get_mcp_browser_profile,
    get_mcp_browser_session,
    with_brand_browser_session,
)
from getgather.parse import parse_html

amazonca_mcp = BrandMCPBase(brand_id="amazonca", name="Amazon CA MCP")


@amazonca_mcp.tool(tags={"private"})
async def get_purchase_history(
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

    browser_profile = get_mcp_browser_profile()
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    purchases, _, _ = await run_distillation_loop(
        f"https://www.amazon.ca/your-orders/orders?timeFilter=year-{target_year}&startIndex={start_index}",
        patterns,
        browser_profile=browser_profile,
        stop_ok=True,
    )
    return {"purchases": purchases}


@amazonca_mcp.tool
@with_brand_browser_session
async def search_product(keyword: str) -> dict[str, Any]:
    """Search product on amazon ca."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto(f"https://www.amazon.ca/s?k={keyword}", wait_until="commit")
    await page.wait_for_selector("div[data-component-type='s-search-result']")

    spec_schema = SpecSchema.model_validate({
        "bundle": "search_results.html",
        "format": "html",
        "output": "search_results.json",
        "row_selector": "div[data-component-type='s-search-result']",
        "extraction_method": "python_parser",
        "columns": [
            {"name": "product_name", "selector": "h2 span"},
            {
                "name": "product_url",
                "selector": "div[data-cy='title-recipe'] a",
                "attribute": "href",
            },
            {"name": "price", "selector": "span.a-price-whole"},
            {"name": "price_fraction", "selector": "span.a-price-fraction"},
            {"name": "currency", "selector": "span.a-price-symbol"},
            {"name": "rating", "selector": "span.a-icon-alt"},
            {"name": "image_url", "selector": "img.s-image", "attribute": "src"},
            {"name": "reviews", "selector": "div[data-cy='reviews-block']"},
        ],
    })

    bundle_result = await parse_html(brand_id=amazonca_mcp.brand_id, schema=spec_schema, page=page)

    return {"product_list": bundle_result.content or []}


@amazonca_mcp.tool
@with_brand_browser_session
async def get_product_detail(ctx: Context, product_url: str) -> dict[str, Any]:
    """Get product detail from amazon ca."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    if not product_url.startswith("https"):
        product_url = f"https://www.amazon.ca/{product_url}"
    await page.goto(product_url)

    await page.wait_for_selector("span#productTitle")
    await page.wait_for_timeout(1000)

    product_data: dict[str, Any] = {}

    title_elem = page.locator("span#productTitle")
    if await title_elem.count() > 0:
        product_data["title"] = await title_elem.inner_text()

    main_image = page.locator("#landingImage, #imgTagWrapperId img")
    if await main_image.count() > 0:
        image_src = await main_image.first.get_attribute("src")
        if image_src:
            product_data["main_image"] = image_src

    feature_bullets = page.locator("#feature-bullets ul li")
    features: list[str] = []
    feature_count = await feature_bullets.count()
    for i in range(min(feature_count, 8)):  # Limit to 8 features
        feature = feature_bullets.nth(i)
        feature_text = await feature.inner_text()
        if feature_text and feature_text.strip():
            features.append(feature_text.strip())
    product_data["features"] = features

    price_elem = page.locator(".a-price .a-offscreen").first
    if await price_elem.count() > 0:
        product_data["price"] = await price_elem.inner_text()

    return {"product_details": product_data}


@amazonca_mcp.tool(tags={"private"})
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from amazon ca."""
    task = (
        "Go to the Amazon cart page and extract cart summary information:\n"
        " 1. Navigate to https://www.amazon.ca/gp/cart/view.html\n"
        " 2. Wait for the page to fully load\n"
        " 3. Extract information about:\n"
        "    - Regular cart items (if any) with titles, prices, quantities\n"
        "    - Local delivery carts (Amazon Fresh, Whole Foods, etc.) with store types, subtotals, item counts\n"
        "    - Overall cart totals and delivery information\n"
        " 4. Return structured data about all cart contents"
    )

    return await run_agent_for_brand(task)


@amazonca_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon ca."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto("https://www.amazon.ca/gp/history?ref_=nav_AccountFlyout_browsinghistory")
    await page.wait_for_timeout(1000)
    await page.wait_for_selector("div[class*='desktop-grid']")
    html = await page.locator("div[class*='desktop-grid']").inner_html()
    return {"browsing_history_html": html}


@amazonca_mcp.tool(tags={"private"})
@with_brand_browser_session
async def search_purchase_history(keyword: str) -> dict[str, Any]:
    """Search purchase history from amazon ca."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto(
        f"https://www.amazon.ca/your-orders/search/ref=ppx_yo2ov_dt_b_search?opt=ab&search={keyword}"
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

    result = await parse_html(brand_id=amazonca_mcp.brand_id, html_content=html, schema=spec_schema)
    return {"order_history": result.content}


@amazonca_mcp.tool(tags={"private"})
async def add_to_cart(ctx: Context, product_url: str, quantity: int = 1) -> dict[str, Any]:
    """Add a product to cart on amazon.ca with specified quantity and options.

    Args:
        product_url: The Amazon product URL or path
        quantity: Number of items to add (default: 1)
    """
    task = (
        "Following the instructions below to add a product to the Amazon cart:\n"
        f" 1. Go to the product page at {product_url if product_url.startswith('https') else 'https://www.amazon.ca' + product_url}.\n"
        " 2. Wait for the page to fully load and verify the product title is visible.\n"
    )

    if quantity > 1:
        task += (
            f" 3. Locate the quantity selector and change it to {quantity}.\n"
            "    - For regular items, look for a dropdown labeled 'Qty:' or similar\n"
            "    - For Fresh/Local delivery items, look for the quantity widget\n"
            "    - If quantity selector shows '10+', click it and enter the exact number\n"
        )

    task += (
        " 4. Find and click 'Add to Cart' button. "
        " 5. After that you're going to be redirected to a new page, or new pop up going to show up. In both cases, there should be 'Added to cart' explanation. if that's the case, then add to cart process is done."
    )

    return await run_agent_for_brand(task)
