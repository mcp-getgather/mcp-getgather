from typing import Any

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, get_mcp_browser_session, with_brand_browser_session
from getgather.parse import parse_html

amazon_mcp = BrandMCPBase(brand_id="amazon", name="Amazon MCP")


@amazon_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get purchase/order history of a amazon."""
    return await extract()


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
        await page.wait_for_timeout(500)

        spec_schema = SpecSchema.model_validate({
            "bundle": "search_results.html",
            "format": "html",
            "output": "search_results.json",
            "row_selector": "div[data-component-type='s-search-result']",
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
            ],
        })

        bundle_result = await parse_html(
            brand_id=amazon_mcp.brand_id, schema=spec_schema, page=page
        )

        return {"product_list": bundle_result.content or []}


@amazon_mcp.tool
async def get_product_detail(
    product_url: str,
) -> dict[str, Any]:
    """Get product detail from amazon.
    Notes that it works better with short product url,
    such as with this format /dp/XXXXXXXXX
    """
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

        # Extract buying options - detect what buttons are available
        buying_options: list[dict[str, Any]] = []

        # Check for regular Amazon add to cart button within buybox
        regular_button = page.locator("#buybox #add-to-cart-button")
        if await regular_button.count() > 0:
            option_data: dict[str, Any] = {"type": "regular", "name": "Amazon"}

            # Try to get price from accordion if available
            regular_option = page.locator("#newAccordionRow_0")
            if await regular_option.count() > 0:
                regular_price = regular_option.locator(".a-price .a-offscreen")
                if await regular_price.count() > 0:
                    option_data["price"] = await regular_price.first.inner_text()

                # Check for delivery restrictions
                delivery_error = regular_option.locator(".a-color-error")
                if await delivery_error.count() > 0:
                    error_text = await delivery_error.first.inner_text()
                    if "cannot be shipped" in error_text.lower():
                        option_data["delivery_restriction"] = error_text.strip()
                        option_data["available"] = False
                    else:
                        option_data["available"] = True
                else:
                    option_data["available"] = True
            else:
                # Use main price if no accordion
                if "price" in product_data:
                    option_data["price"] = product_data["price"]
                option_data["available"] = True

            buying_options.append(option_data)

        # Check for local delivery (fresh) add to cart button (delivery, not pickup)
        fresh_button = page.locator("#buybox #almAddToCart_feature_div #freshAddToCartButton")
        if await fresh_button.count() > 0:
            option_data: dict[str, Any] = {"type": "local_delivery"}

            # Try to get info from accordion first (if it exists)
            local_option = page.locator("#almAccordionRow")
            if await local_option.count() > 0:
                # Accordion-based local delivery
                local_price = local_option.locator(".a-price .a-offscreen")
                if await local_price.count() > 0:
                    option_data["price"] = await local_price.first.inner_text()

                # Get delivery message
                delivery_message = local_option.locator("#alm-delivery-message").first
                if await delivery_message.count() > 0:
                    delivery_text = await delivery_message.inner_text()
                    option_data["delivery_info"] = delivery_text.strip()

                # Get store/brand name from logo alt text
                logo_elem = local_option.locator("#almLogo").first
                if await logo_elem.count() > 0:
                    logo_alt = await logo_elem.get_attribute("alt")
                    if logo_alt:
                        option_data["name"] = logo_alt

                # Fallback: get name from "Ships from" text
                if "name" not in option_data:
                    ships_from = local_option.locator(
                        ".sfsb-header-text span:has-text('Ships from:') + span"
                    )
                    if await ships_from.count() > 0:
                        store_name = await ships_from.inner_text()
                        option_data["name"] = store_name.strip()
                    else:
                        option_data["name"] = "Local Store"
            else:
                # Single local delivery option (no accordion) - use main price
                if "price" in product_data:
                    option_data["price"] = product_data["price"]

                # Just use "Local Store" for single option cases
                option_data["name"] = "Local Store"

                option_data["delivery_info"] = "Local delivery available"

            option_data["available"] = True
            buying_options.append(option_data)

        product_data["buying_options"] = buying_options

        return {"product_details": product_data}


@amazon_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from amazon."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/cart/view.html")
    await page.wait_for_timeout(2000)

    cart_summary: dict[str, Any] = {
        "local_carts": [],
        "regular_cart": None,
        "total_items": 0,
        "total_amount": "0.00",
    }

    # Extract Local delivery carts (Fresh, Whole Foods, etc.) if present
    local_carts_container = "div#sc-collapsed-carts-container"
    if await page.locator(local_carts_container).count() > 0:
        # Find all individual local market carts
        local_cart_divs = page.locator(f"{local_carts_container} div[id^='sc-localmarket-cart-']")
        local_cart_count = await local_cart_divs.count()

        for i in range(local_cart_count):
            local_cart_div = local_cart_divs.nth(i)
            local_cart_data: dict[str, Any] = {}

            # Get cart type/store name from the cart div classes or content
            cart_classes = await local_cart_div.get_attribute("class") or ""
            if "sc-localmarket-fresh" in cart_classes:
                local_cart_data["store_type"] = "Amazon Fresh"
            elif "sc-branded-cart-container-VUZHIFdob2xlIUZvb2Rz" in cart_classes:
                local_cart_data["store_type"] = "Whole Foods"
            else:
                local_cart_data["store_type"] = "Local Store"

            # Get subtotal for this specific cart
            subtotal_elem = local_cart_div.locator("span#sc-subtotal-amount-buybox .sc-price")
            if await subtotal_elem.count() > 0:
                subtotal = await subtotal_elem.first.inner_text()
                local_cart_data["subtotal"] = subtotal.strip()

            # Get item count for this specific cart
            count_elem = local_cart_div.locator("span#sc-subtotal-label-buybox")
            if await count_elem.count() > 0:
                count_text = await count_elem.first.inner_text()
                local_cart_data["items_text"] = count_text.strip()

            # Get delivery info if available
            delivery_elem = local_cart_div.locator(".sc-fresh-delivery-threshold")
            if await delivery_elem.count() > 0:
                delivery_info = await delivery_elem.first.inner_text()
                local_cart_data["delivery_info"] = delivery_info.strip()

            # Get items for this specific cart
            local_items: list[dict[str, Any]] = []
            item_images = local_cart_div.locator(".sc-collapsed-item-thumbnails img")
            item_count = await item_images.count()
            for j in range(item_count):
                item_img = item_images.nth(j)
                alt_text = await item_img.get_attribute("alt")
                src = await item_img.get_attribute("src")
                if alt_text:
                    local_items.append({"name": alt_text, "image_url": src})
            local_cart_data["items"] = local_items

            cart_summary["local_carts"].append(local_cart_data)

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


@amazon_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_browsing_history() -> dict[str, Any]:
    """Get browsing history from amazon."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/history?ref_=nav_AccountFlyout_browsinghistory")
    await page.wait_for_timeout(1000)
    await page.wait_for_selector("div[class*='desktop-grid']")
    html = await page.locator("div[class*='desktop-grid']").inner_html()
    return {"browsing_history_html": html}


@amazon_mcp.tool(tags={"private"})
@with_brand_browser_session
async def search_purchase_history(
    keyword: str,
) -> dict[str, Any]:
    """Search purchase history of a amazon."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()
    await page.goto(
        f"https://www.amazon.com/your-orders/search/ref=ppx_yo2ov_dt_b_search?opt=ab&search={keyword}"
    )
    await page.wait_for_selector("div.a-section.a-spacing-none.a-padding-small")
    await page.wait_for_timeout(1000)

    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.a-section.a-spacing-large.a-spacing-top-large",
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

    result = await parse_html(brand_id=amazon_mcp.brand_id, schema=spec_schema, page=page)
    return {"order_history": result.content}


@amazon_mcp.tool(tags={"private"})
@with_brand_browser_session
async def add_to_cart(
    product_url: str,
    quantity: int = 1,
    variant_asin: str | None = None,
    buying_option: str = "regular",
) -> dict[str, Any]:
    """Add a product to cart on Amazon with specified quantity.

    Args:
        product_url: The Amazon product URL or path
        quantity: Number of items to add (default: 1)
        variant_asin: Optional ASIN for specific variant (size, color, etc.)
        buying_option: Which buying option to use ("regular" or "local_delivery") (default: "regular")
    """
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()

    # Navigate to product page
    if not product_url.startswith("https"):
        product_url = f"https://www.amazon.com/{product_url}"
    await page.goto(product_url)

    # Wait for product page to load
    await page.wait_for_selector("span#productTitle")
    await page.wait_for_timeout(500)

    result: dict[str, Any] = {"success": False, "message": ""}

    try:
        # Get product title for confirmation
        title_elem = page.locator("span#productTitle")
        product_title = ""
        if await title_elem.count() > 0:
            product_title = await title_elem.inner_text()
            result["product_title"] = product_title.strip()

        # Select variant if specified
        if variant_asin:
            # Look for variant selector with the specific ASIN
            variant_selector = f"li[data-asin='{variant_asin}']"
            variant_elem = page.locator(variant_selector)

            if await variant_elem.count() > 0:
                # Check if this variant is already selected
                is_selected = await variant_elem.get_attribute("data-initiallyselected") == "true"

                if not is_selected:
                    # Click on the variant to select it only if not already selected
                    await variant_elem.click()
                    # Verify the variant was actually selected
                    await variant_elem.wait_for(state="attached")
                    result["variant_selected"] = variant_asin
                else:
                    # Variant is already selected, no need to click
                    result["variant_selected"] = variant_asin

                # Get variant name if available
                variant_name = variant_elem.locator(".swatch-title-text")
                if await variant_name.count() > 0:
                    result["variant_name"] = await variant_name.inner_text()
            else:
                result["message"] = f"Variant with ASIN {variant_asin} not found"
                result["variant_selected"] = None

        # Check if the add to cart button for the selected buying option is available
        if buying_option == "local_delivery":
            # Check if fresh delivery button is visible
            fresh_button_check = page.locator(
                "#buybox #almAddToCart_feature_div #freshAddToCartButton"
            )
            if await fresh_button_check.count() == 0 or not await fresh_button_check.is_visible():
                result["message"] = (
                    f"Local delivery add to cart button is not available. Please use buying_option='regular' instead."
                )
                result["error"] = "buying_option_not_available"
                return result
            result["buying_option_selected"] = "local_delivery"
        else:
            # Check if regular button is visible
            regular_button_check = page.locator("#buybox #add-to-cart-button")
            if (
                await regular_button_check.count() == 0
                or not await regular_button_check.is_visible()
            ):
                result["message"] = (
                    f"Regular delivery add to cart button is not available. Please use buying_option='local_delivery' instead."
                )
                result["error"] = "buying_option_not_available"
                return result
            result["buying_option_selected"] = "regular"

        # Helper function for keyboard navigation and quantity verification
        async def select_quantity_with_keyboard(
            qty_button: Any, target_qty: int, max_attempts: int | None = None
        ) -> int:
            """
            Navigate to a quantity using keyboard and return the actual selected quantity.

            Args:
                qty_button: The quantity button locator
                target_qty: The desired quantity to select
                max_attempts: Maximum number of down arrow presses (default: target_qty - 1)

            Returns:
                int: The actual quantity that was selected
            """
            if max_attempts is None:
                max_attempts = target_qty - 1

            # Navigate using arrow keys
            for _ in range(max_attempts):
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(100)

            # Press Enter to select
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(300)

            # Check what was actually selected
            try:
                qty_text = await qty_button.inner_text()
                if ":" in qty_text:
                    return int(qty_text.split(":")[1].strip())
                elif qty_text.isdigit():
                    return int(qty_text)
                else:
                    import re

                    numbers = re.findall(r"\d+", qty_text)
                    if numbers:
                        return int(numbers[0])
            except:
                pass
            return 1  # Default if we can't parse

        # Now select quantity within the chosen buying option context
        if buying_option == "local_delivery" and quantity > 1:
            # Fresh/Local delivery quantity selector (qs-widget) - after selecting buying option
            # Target the delivery-specific quantity widget, not pickup
            fresh_qty_button = page.locator(
                "#almAddToCart_feature_div button[id^='qs-widget-button-'][id$='-announce']"
            )

            if await fresh_qty_button.count() > 0:
                # Click the quantity button to open dropdown
                await fresh_qty_button.click()
                await page.wait_for_timeout(500)

                if quantity < 10:
                    # For quantities 1-9, use keyboard navigation to select the option
                    # This avoids scrolling issues in the dropdown
                    try:
                        actual_quantity = await select_quantity_with_keyboard(
                            fresh_qty_button, quantity
                        )
                        result["quantity_selected"] = actual_quantity

                        if actual_quantity < quantity:
                            result["message"] = (
                                f"Added {actual_quantity} item(s) to cart (requested {quantity}, but only {actual_quantity} available in stock)"
                            )
                            result["stock_limited"] = True
                        else:
                            result["message"] = f"Added {actual_quantity} item(s) to cart"
                    except Exception:
                        # Fallback if keyboard navigation fails
                        result["quantity_selected"] = 1
                else:
                    # For quantities 10+, click the "10+" option first then use text input
                    # Scope to the delivery-specific dropdown
                    ten_plus_option = page.locator(
                        "#almAddToCart_feature_div ul[id^='qs-widget-dropdown-unorderedlist-'] li:has-text('10+')"
                    )
                    if await ten_plus_option.count() > 0:
                        # Scroll the "10+" option into view within the dropdown before clicking
                        await ten_plus_option.scroll_into_view_if_needed()
                        await ten_plus_option.click()
                        await page.wait_for_timeout(500)

                        # Now use the text input method
                        qty_text_input = page.locator(
                            "#almAddToCart_feature_div input[id^='qs-widget-text-input-']"
                        )
                        if await qty_text_input.count() > 0:
                            await qty_text_input.fill(str(quantity))
                            # Click update button
                            update_button = page.locator(
                                "#almAddToCart_feature_div button[id^='qs-widget-text-input-updatelink-'][id$='-announce']"
                            )
                            if await update_button.count() > 0:
                                await update_button.click()
                            result["quantity_selected"] = quantity
                        else:
                            result["quantity_selected"] = 1
                    else:
                        # No "10+" option available, which means max is less than 10
                        # Fall back to keyboard navigation for the maximum available
                        try:
                            # Try to select up to 9 (press down 8 times from 1)
                            actual_quantity = await select_quantity_with_keyboard(
                                fresh_qty_button, quantity, max_attempts=8
                            )
                            result["quantity_selected"] = actual_quantity
                            result["message"] = (
                                f"Added {actual_quantity} item(s) to cart (requested {quantity}, but only {actual_quantity} available in stock)"
                            )
                            result["stock_limited"] = True
                        except:
                            result["quantity_selected"] = 1
                await page.wait_for_timeout(500)
            else:
                result["quantity_selected"] = 1

        elif buying_option == "regular" and quantity > 1:
            # Regular quantity selector (dropdown popover) - after selecting buying option
            regular_qty_selector = page.locator("#quantity")

            if await regular_qty_selector.count() > 0:
                current_quantity = await regular_qty_selector.input_value()

                if current_quantity != str(quantity):
                    # Click the quantity dropdown button to open the popover
                    quantity_dropdown_button = page.locator(
                        "#selectQuantity .a-button-dropdown"
                    ).first
                    if await quantity_dropdown_button.count() > 0:
                        await quantity_dropdown_button.click()
                        await page.wait_for_timeout(500)

                        # Find and click the quantity option in the popover
                        # The quantity options are numbered starting from 0, so quantity 20 is id="quantity_19"
                        quantity_option = page.locator(f"#quantity_{quantity - 1}")
                        if await quantity_option.count() > 0:
                            await quantity_option.click()
                            await page.wait_for_timeout(500)
                            # Verify the quantity was actually selected
                            new_quantity = await regular_qty_selector.input_value()
                            result["quantity_selected"] = (
                                int(new_quantity) if new_quantity.isdigit() else 1
                            )
                        else:
                            result["quantity_selected"] = 1
                    else:
                        result["quantity_selected"] = 1
                else:
                    # Quantity already matches target
                    result["quantity_selected"] = quantity
            else:
                # No quantity selector found - this product doesn't support quantity selection
                result["quantity_selected"] = 1
                if quantity > 1:
                    result["message"] = (
                        f"Added 1 item to cart (requested {quantity}, but this product doesn't support quantity selection - only 1 item can be added at a time)"
                    )
                    result["stock_limited"] = True
        else:
            # Quantity is 1 or no quantity change needed
            result["quantity_selected"] = quantity if quantity == 1 else 1

        # Determine which button to click based on buying option (already validated above)
        if buying_option == "local_delivery":
            # Use fresh delivery button (already validated as available)
            add_to_cart_button = page.locator(
                "#buybox #almAddToCart_feature_div #freshAddToCartButton"
            )
        else:
            # Use regular Amazon delivery button (already validated as available)
            add_to_cart_button = page.locator("#buybox #add-to-cart-button")
        if await add_to_cart_button.count() > 0:
            await add_to_cart_button.click()
            await page.wait_for_timeout(1000)

            # Check if we're redirected to cart
            current_url = page.url
            if "cart" in current_url.lower():
                result["success"] = True
                # Don't override the message if we already set a stock-limited message
                if "stock_limited" not in result:
                    result["message"] = f"Successfully added {quantity} item(s) to cart"
                result["redirected_to_cart"] = True
            else:
                # Assume success if no redirect (item added without going to cart page)
                result["success"] = True
                # Don't override the message if we already set a stock-limited message
                if "stock_limited" not in result:
                    result["message"] = f"Added {quantity} item(s) to cart"
                result["redirected_to_cart"] = False
        else:
            result["message"] = "Add to Cart button not found"

    except Exception as e:
        result["message"] = f"Error during add to cart: {str(e)}"
        result["error"] = str(e)

    return result
