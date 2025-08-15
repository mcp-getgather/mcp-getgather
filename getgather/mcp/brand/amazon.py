from typing import Any

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract
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
        await page.goto(f"https://www.amazon.com/s?k={keyword}", wait_until="commit")
        await page.wait_for_selector("div[data-component-type='s-search-result']")
        await page.wait_for_timeout(1000)

        spec_schema = SpecSchema.model_validate({
            "bundle": "search_results.html",
            "format": "html",
            "output": "search_results.json",
            "row_selector": "div[data-component-type='s-search-result']",
            "columns": [
                {"name": "product_name", "selector": "h2 span"},
                {
                    "name": "product_url",
                    "selector": "a.s-line-clamp-2",
                    "attribute": "href",
                },
                {"name": "price", "selector": "span.a-price-whole"},
                {"name": "price_fraction", "selector": "span.a-price-fraction"},
                {"name": "currency", "selector": "span.a-price-symbol"},
                {"name": "rating", "selector": "span.a-icon-alt"},
                {"name": "review_count", "selector": "span.a-size-base.s-underline-text"},
                {"name": "prime", "selector": "i.a-icon-prime"},
                {"name": "image_url", "selector": "img.s-image", "attribute": "src"},
            ],
        })

        bundle_result = await parse_html(
            brand_id=BrandIdEnum("amazon"), schema=spec_schema, page=page
        )

        return {"product_list": bundle_result.content or []}


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

        product_data: dict[str, Any] = {}

        title_elem = page.locator("span#productTitle")
        if await title_elem.count() > 0:
            product_data["title"] = await title_elem.inner_text()

        main_image = page.locator("#landingImage, #imgTagWrapperId img")
        if await main_image.count() > 0:
            image_src = await main_image.first.get_attribute("src")
            if image_src:
                product_data["main_image"] = image_src

        variants: list[dict[str, Any]] = []
        variant_lists = page.locator("ul.dimension-values-list")
        variant_count = await variant_lists.count()

        for i in range(variant_count):
            variant_list = variant_lists.nth(i)
            variant_items = variant_list.locator("li")
            item_count = await variant_items.count()

            for j in range(min(item_count, 10)):
                item = variant_items.nth(j)

                variant_data: dict[str, Any] = {}

                asin = await item.get_attribute("data-asin")
                if asin:
                    variant_data["asin"] = asin

                variant_text = item.locator(".swatch-title-text")
                if await variant_text.count() > 0:
                    variant_data["name"] = await variant_text.inner_text()

                price_elem = item.locator(".a-price .a-offscreen, .a-price[aria-hidden='true']")
                if await price_elem.count() > 0:
                    variant_data["price"] = await price_elem.first.inner_text()

                availability = item.locator("#twisterAvailability")
                if await availability.count() > 0:
                    variant_data["availability"] = await availability.inner_text()

                selected = await item.get_attribute("data-initiallyselected")
                variant_data["selected"] = selected == "true"

                if variant_data:
                    variants.append(variant_data)

        product_data["variants"] = variants

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


@amazon_mcp.tool(tags={"private"})
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from amazon."""
<<<<<<< HEAD
    browser_session = await start_browser_session(brand_id=amazon_mcp.brand_id)
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/cart/view.html")
    await page.wait_for_selector("div#sc-active-cart")
    await page.wait_for_timeout(1000)
    html = await page.locator("div#sc-active-cart").inner_html()
    return {"cart_summary_html": html}
=======
    profile_id = BrandState.get_browser_profile_id(BrandIdEnum("amazon"))
    profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto("https://www.amazon.com/gp/cart/view.html")
        await page.wait_for_timeout(2000)

        cart_summary: dict[str, Any] = {
            "fresh_cart": None,
            "regular_cart": None,
            "total_items": 0,
            "total_amount": "0.00",
        }

        # Extract Fresh cart if present
        fresh_cart_selector = "div#sc-collapsed-carts-container"
        if await page.locator(fresh_cart_selector).count() > 0:
            fresh_cart_data: dict[str, Any] = {}

            fresh_subtotal_selector = (
                f"{fresh_cart_selector} span#sc-subtotal-amount-buybox .sc-price"
            )
            if await page.locator(fresh_subtotal_selector).count() > 0:
                fresh_subtotal = await page.locator(fresh_subtotal_selector).inner_text()
                fresh_cart_data["subtotal"] = fresh_subtotal.strip()

            fresh_count_selector = f"{fresh_cart_selector} span#sc-subtotal-label-buybox"
            if await page.locator(fresh_count_selector).count() > 0:
                fresh_count_text = await page.locator(fresh_count_selector).inner_text()
                fresh_cart_data["items_text"] = fresh_count_text.strip()

            delivery_threshold_selector = f"{fresh_cart_selector} .sc-fresh-delivery-threshold"
            if await page.locator(delivery_threshold_selector).count() > 0:
                delivery_info = await page.locator(delivery_threshold_selector).inner_text()
                fresh_cart_data["delivery_info"] = delivery_info.strip()

            fresh_items: list[dict[str, Any]] = []
            fresh_item_images = page.locator(
                f"{fresh_cart_selector} .sc-collapsed-item-thumbnails img"
            )
            count = await fresh_item_images.count()
            for i in range(count):
                item_img = fresh_item_images.nth(i)
                alt_text = await item_img.get_attribute("alt")
                src = await item_img.get_attribute("src")
                if alt_text:
                    fresh_items.append({"name": alt_text, "image_url": src})
            fresh_cart_data["items"] = fresh_items

            cart_summary["fresh_cart"] = fresh_cart_data

        # Extract Regular cart if present
        regular_subtotal_selector = "span#sc-subtotal-amount-activecart .sc-price"
        if await page.locator(regular_subtotal_selector).count() > 0:
            regular_cart_data: dict[str, Any] = {}

            regular_subtotal = await page.locator(regular_subtotal_selector).inner_text()
            regular_cart_data["subtotal"] = regular_subtotal.strip()

            regular_count_selector = "span#sc-subtotal-label-activecart"
            if await page.locator(regular_count_selector).count() > 0:
                regular_count_text = await page.locator(regular_count_selector).inner_text()
                regular_cart_data["items_text"] = regular_count_text.strip()

            regular_items: list[dict[str, Any]] = []
            item_rows = page.locator("div.sc-list-item[data-itemtype='active'][data-asin]")
            count = await item_rows.count()

            for i in range(count):
                item_row = item_rows.nth(i)
                item_data: dict[str, Any] = {}

                title_selector = ".sc-product-title span.a-truncate-full"
                if await item_row.locator(title_selector).count() > 0:
                    title = await item_row.locator(title_selector).first.inner_text()
                    item_data["title"] = title.strip()

                price_selector = ".apex-price-to-pay-value"
                if await item_row.locator(price_selector).count() > 0:
                    price = await item_row.locator(price_selector).first.inner_text()
                    item_data["price"] = price.strip()

                availability_selector = ".sc-product-availability"
                if await item_row.locator(availability_selector).count() > 0:
                    availability = await item_row.locator(availability_selector).inner_text()
                    item_data["availability"] = availability.strip()

                delivery_selector = ".udm-delivery-block"
                if await item_row.locator(delivery_selector).count() > 0:
                    delivery = await item_row.locator(delivery_selector).inner_text()
                    item_data["delivery"] = delivery.strip()

                image_selector = "img.sc-product-image"
                if await item_row.locator(image_selector).count() > 0:
                    image_src = await item_row.locator(image_selector).get_attribute("src")
                    item_data["image_url"] = image_src

                qty_selector = "fieldset[name='sc-quantity'] span[data-a-selector='value']"
                if await item_row.locator(qty_selector).count() > 0:
                    qty = await item_row.locator(qty_selector).inner_text()
                    item_data["quantity"] = qty.strip()

                asin = await item_row.get_attribute("data-asin")
                if asin:
                    item_data["asin"] = asin

                if item_data:
                    regular_items.append(item_data)

            regular_cart_data["items"] = regular_items
            cart_summary["regular_cart"] = regular_cart_data

        return cart_summary
>>>>>>> 7044303 (Fix amazon tools)


@amazon_mcp.tool(tags={"private"})
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon."""
<<<<<<< HEAD
    browser_session = await start_browser_session(brand_id=amazon_mcp.brand_id)
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/history?ref_=nav_AccountFlyout_browsinghistory")
    await page.wait_for_timeout(1000)
    await page.wait_for_selector("div[class*='desktop-grid']")
    html = await page.locator("div[class*='desktop-grid']").inner_html()
    return {"browsing_history_html": html}
=======
    profile_id = BrandState.get_browser_profile_id(BrandIdEnum("amazon"))
    profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto("https://www.amazon.com/gp/history?ref_=nav_AccountFlyout_browsinghistory")
        await page.wait_for_timeout(1000)
        await page.wait_for_selector("div[class*='desktop-grid']")
        html = await page.locator("div[class*='desktop-grid']").inner_html()
        return {"browsing_history_html": html}
>>>>>>> 7044303 (Fix amazon tools)
