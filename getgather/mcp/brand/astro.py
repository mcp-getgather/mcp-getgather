from typing import Any, cast
from urllib.parse import quote

from patchright.async_api import Locator

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract
from getgather.parse import parse_html

astro_mcp = BrandMCPBase(prefix="astro", name="Astro MCP")


@astro_mcp.tool(tags={"private"})
async def get_purchase_history() -> dict[str, Any]:
    """Get astro purchase history."""
    return await extract(brand_id=BrandIdEnum("astro"))


@astro_mcp.tool
async def search_product(
    keyword: str,
) -> dict[str, Any]:
    """Search product on astro."""
    if BrandState.is_brand_connected(BrandIdEnum("astro")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("astro"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        # URL encode the search keyword
        encoded_keyword = quote(keyword)
        await page.goto(
            f"https://www.astronauts.id/search?q={encoded_keyword}", wait_until="commit"
        )
        await page.wait_for_selector("div[data-testid='srp-main']")
        await page.wait_for_timeout(2000)
        html = await page.locator("div[data-testid='srp-main']").inner_html()

    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.MuiGrid-item.MuiGrid-grid-xs-4.css-qdep8d",
        "columns": [
            {"name": "product_name", "selector": "span.MuiTypography-paragraph-tiny.css-xkitcr"},
            {"name": "product_url", "selector": "a[href^='/p/']", "attribute": "href"},
            {"name": "price", "selector": "span.MuiTypography-body-smallStrong.css-e2mums"},
            {"name": "product_size", "selector": "span.MuiTypography-caption-tiny.css-1mxh19w"},
            {
                "name": "product_image",
                "selector": "img.image[src*='image.astronauts.cloud']",
                "attribute": "src",
            },
            {
                "name": "discount_percentage",
                "selector": "span.MuiTypography-caption-tinyBold.css-1xzi4v7",
            },
            {
                "name": "original_price",
                "selector": "span.MuiTypography-caption-tiny.css-1mxh19w[style*='line-through']",
            },
            {"name": "stock_status", "selector": "span.MuiTypography-caption-tiny.css-1lb2yr7"},
        ],
    })
    result = await parse_html(brand_id=BrandIdEnum("astro"), html_content=html, schema=spec_schema)
    return {"product_list": result.content}


@astro_mcp.tool
async def get_product_details(
    product_url: str,
) -> dict[str, Any]:
    """Get product detail from astro. Get product_url from search_product tool."""
    if BrandState.is_brand_connected(BrandIdEnum("astro")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("astro"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto(full_url, wait_until="commit")
        await page.wait_for_selector("main.MuiBox-root")
        await page.wait_for_timeout(1000)
        html = await page.locator("body").inner_html()

    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "main.MuiBox-root",
        "columns": [
            {"name": "product_title", "selector": "h1[data-testid='pdp-title']"},
            {"name": "price", "selector": "p[data-testid='pdp-price']"},
            {"name": "description", "selector": "span[data-testid='pdp-description-content']"},
            {
                "name": "expiry_date",
                "selector": "div[data-testid='pdp-expiry-section'] span.MuiTypography-caption-small",
            },
            {
                "name": "return_condition",
                "selector": "div[data-testid='pdp-retur-message'] span.MuiTypography-caption-small",
            },
            {"name": "product_image", "selector": "img.image", "attribute": "src"},
            {"name": "add_to_cart_available", "selector": "button[data-testid='pdp-atc-btn']"},
        ],
    })
    result = await parse_html(brand_id=BrandIdEnum("astro"), html_content=html, schema=spec_schema)

    product_details: dict[str, Any] = (
        result.content[0] if result.content and len(result.content) > 0 else {}
    )

    return {"product_details": product_details}


@astro_mcp.tool(tags={"private"})
async def update_cart_item(
    product_url: str,
    quantity: int = 1,
) -> dict[str, Any]:
    """Update cart item quantity on astro (add new item or update existing quantity). Get product_url from search_product tool."""
    profile_id = BrandState.get_browser_profile_id(BrandIdEnum("astro"))
    profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()

    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto(full_url, wait_until="commit")
        await page.wait_for_selector("main.MuiBox-root")
        await page.wait_for_timeout(1000)

        # Check if quantity controls already exist (item already in cart)
        quantity_controls = page.locator("div.MuiBox-root.css-1aek3i0")
        is_already_in_cart = await quantity_controls.is_visible()

        if is_already_in_cart:
            current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")
            current_quantity_text = await current_quantity_element.text_content()
            current_quantity = int(current_quantity_text or "0")

            quantity_diff = quantity - current_quantity

            if quantity_diff > 0:
                plus_button = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(
                    1
                )  # Second button (plus)
                for _ in range(quantity_diff):
                    await plus_button.click()
                    await page.wait_for_timeout(300)
            elif quantity_diff < 0:
                minus_button = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(
                    0
                )  # First button (minus)
                for _ in range(abs(quantity_diff)):
                    await minus_button.click()
                    await page.wait_for_timeout(300)

            final_quantity_text = await current_quantity_element.text_content()
            final_quantity = int(final_quantity_text or "0")

            return {
                "success": True,
                "message": f"Updated quantity from {current_quantity} to {final_quantity} item(s)",
                "previous_quantity": current_quantity,
                "final_quantity": final_quantity,
                "quantity_changed": quantity_diff,
                "product_url": full_url,
                "action": "quantity_updated",
            }
        else:
            # Item not in cart, check if add to cart button exists
            add_to_cart_button = page.locator("button[data-testid='pdp-atc-btn']")
            if not await add_to_cart_button.is_visible():
                return {
                    "success": False,
                    "error": "Add to cart button not found or product not available",
                }

            await add_to_cart_button.click()
            await page.wait_for_timeout(1000)

            # Wait for quantity controls to appear
            await quantity_controls.wait_for(state="visible", timeout=5000)

            if quantity > 1:
                plus_button: Locator = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(
                    1
                )
                for _ in range(quantity - 1):
                    await plus_button.click()
                    await page.wait_for_timeout(500)

            current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")
            final_quantity_text = await current_quantity_element.text_content()
            final_quantity = int(final_quantity_text or "0")

            return {
                "success": True,
                "message": f"Successfully added {final_quantity} item(s) to cart",
                "previous_quantity": 0,
                "final_quantity": final_quantity,
                "quantity_changed": final_quantity,
                "product_url": full_url,
                "action": "added_to_cart",
            }


@astro_mcp.tool(tags={"private"})
async def update_cart_quantity(
    product_name: str,
    quantity: int,
) -> dict[str, Any]:
    """Update cart item quantity on astro (set quantity to 0 to remove item). Use product name from cart summary."""
    profile_id = BrandState.get_browser_profile_id(BrandIdEnum("astro"))
    profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto("https://www.astronauts.id/cart", wait_until="commit")
        await page.wait_for_selector("main.MuiBox-root")
        await page.wait_for_timeout(2000)

        # Find the cart item by product name
        cart_item_selector = f"//span[contains(@class, 'MuiTypography-body-default') and contains(text(), '{product_name}')]/ancestor::div[contains(@class, 'css-bnftmf')]"
        cart_item = page.locator(cart_item_selector)

        if not await cart_item.is_visible():
            return {
                "success": False,
                "message": f"Product '{product_name}' not found in cart",
                "product_name": product_name,
                "action": "update_failed",
            }

        quantity_controls = cart_item.locator("div.MuiBox-root.css-1aek3i0")
        if not await quantity_controls.is_visible():
            return {
                "success": False,
                "message": f"Quantity controls not found for '{product_name}'",
                "product_name": product_name,
                "action": "update_failed",
            }

        # Get current quantity
        current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")
        current_quantity_text = await current_quantity_element.text_content()
        current_quantity = int(current_quantity_text or "0")

        quantity_diff = quantity - current_quantity

        if quantity_diff > 0:
            plus_button = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(
                1
            )  # Second button (plus)
            for _ in range(quantity_diff):
                await plus_button.click()
                await page.wait_for_timeout(500)
        elif quantity_diff < 0:
            minus_button = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(
                0
            )  # First button (minus)
            for _ in range(abs(quantity_diff)):
                await minus_button.click()
                await page.wait_for_timeout(500)

        # Wait for update to complete
        await page.wait_for_timeout(1000)

        final_quantity = 0
        if quantity > 0:
            try:
                final_quantity_text = await current_quantity_element.text_content()
                final_quantity = int(final_quantity_text or "0")
            except:
                final_quantity = 0

        action = "removed_from_cart" if quantity == 0 else "quantity_updated"
        message = (
            f"Removed '{product_name}' from cart"
            if quantity == 0
            else f"Updated '{product_name}' quantity from {current_quantity} to {final_quantity}"
        )

        return {
            "success": True,
            "message": message,
            "previous_quantity": current_quantity,
            "final_quantity": final_quantity,
            "quantity_changed": quantity_diff,
            "product_name": product_name,
            "action": action,
        }


@astro_mcp.tool(tags={"private"})
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from astro."""
    profile_id = BrandState.get_browser_profile_id(BrandIdEnum("astro"))
    profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto("https://www.astronauts.id/cart", wait_until="commit")
        await page.wait_for_selector("main.MuiBox-root")
        await page.wait_for_timeout(5000)
        html = await page.locator("body").inner_html()

    # Extract available items using selector-based parsing
    available_items_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.MuiBox-root.css-bnftmf div.MuiBox-root.css-1msuw7t",
        "columns": [
            {
                "name": "name",
                "selector": "div.MuiBox-root.css-j7qwjs span.MuiTypography-body-default",
            },
            {"name": "image_url", "selector": "img.MuiBox-root.css-1jmoofa", "attribute": "src"},
            {
                "name": "quantity",
                "selector": "div.MuiBox-root.css-1aek3i0 span.MuiTypography-body-small",
            },
            {
                "name": "current_price",
                "selector": "div.MuiBox-root.css-0:last-child p.MuiTypography-body-default.css-133xbhx",
            },
            {
                "name": "original_price",
                "selector": "div.MuiBox-root.css-0:last-child span.MuiTypography-body-default.css-1bb6qij",
            },
            {
                "name": "discount_percentage",
                "selector": "div.css-6qgay2 span.MuiTypography-caption-tiny",
            },
        ],
    })

    available_items_result = await parse_html(
        brand_id=BrandIdEnum("astro"), html_content=html, schema=available_items_schema
    )

    # Extract unavailable items using selector-based parsing
    unavailable_items_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.MuiBox-root.css-g89h0y div.MuiBox-root.css-1msuw7t",
        "columns": [
            {
                "name": "name",
                "selector": "div.MuiBox-root.css-j7qwjs span.MuiTypography-body-default",
            },
            {"name": "image_url", "selector": "img.MuiBox-root.css-1jmoofa", "attribute": "src"},
            {
                "name": "quantity",
                "selector": "div.MuiBox-root.css-1bmdty span.MuiTypography-body-small",
            },
        ],
    })

    unavailable_items_result = await parse_html(
        brand_id=BrandIdEnum("astro"), html_content=html, schema=unavailable_items_schema
    )

    # Extract totals using selector-based parsing
    summary_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.MuiBox-root.css-4kor8h",
        "columns": [
            {
                "name": "subtotal",
                "selector": "div.MuiBox-root.css-1duxxgg:first-child span:last-child",
            },
            {
                "name": "shipping_fee",
                "selector": "div.MuiBox-root.css-1duxxgg:nth-child(2) div.MuiBox-root.css-171onha:last-child span:last-child",
            },
            {
                "name": "service_fee",
                "selector": "div.MuiBox-root.css-1duxxgg:last-child span:last-child",
            },
        ],
    })

    summary_result = await parse_html(
        brand_id=BrandIdEnum("astro"), html_content=html, schema=summary_schema
    )

    # Extract final total
    total_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.MuiBox-root.css-1ia6xgx",
        "columns": [
            {
                "name": "total_amount",
                "selector": "div.MuiBox-root.css-axw7ok span.MuiTypography-body-default.css-g3g47m",
            },
            {"name": "savings", "selector": "div.css-n6k44k span.MuiTypography-caption-tinyBold"},
        ],
    })

    total_result = await parse_html(
        brand_id=BrandIdEnum("astro"), html_content=html, schema=total_schema
    )

    # Process available items
    available_items: list[dict[str, Any]] = []
    available_content: list[Any] = available_items_result.content or []
    for item in available_content:
        if not isinstance(item, dict):
            continue
        item_dict: dict[str, Any] = cast(dict[str, Any], item)
        available_items.append({
            "name": item_dict.get("name", ""),
            "quantity": int(item_dict.get("quantity", "1")),
            "price": item_dict.get("current_price", ""),
            "original_price": item_dict.get("original_price"),
            "image_url": item_dict.get("image_url", ""),
            "status": "available",
            "discount_percentage": item_dict.get("discount_percentage", "0%"),
        })

    # Process unavailable items
    unavailable_items: list[dict[str, Any]] = []
    unavailable_content: list[Any] = unavailable_items_result.content or []
    for item in unavailable_content:
        if not isinstance(item, dict):
            continue
        unavail_item_dict: dict[str, Any] = cast(dict[str, Any], item)
        unavailable_items.append({
            "name": unavail_item_dict.get("name", ""),
            "quantity": int(unavail_item_dict.get("quantity", "1")),
            "image_url": unavail_item_dict.get("image_url", ""),
            "status": "unavailable",
            "reason": "Cannot be processed",
        })

    # Build summary
    summary_data: dict[str, Any] = summary_result.content[0] if summary_result.content else {}
    total_data: dict[str, Any] = total_result.content[0] if total_result.content else {}

    summary: dict[str, Any] = {
        "total_items": len(available_items) + len(unavailable_items),
        "available_items": len(available_items),
        "unavailable_items": len(unavailable_items),
        "subtotal": summary_data.get("subtotal", "Rp0"),
        "shipping_fee": summary_data.get("shipping_fee", "Rp0"),
        "service_fee": summary_data.get("service_fee", "Rp0"),
        "total_amount": total_data.get("total_amount", "Rp0"),
        "savings": total_data.get("savings", ""),
    }

    return {
        "items": available_items + unavailable_items,
        "available_items": available_items,
        "unavailable_items": unavailable_items,
        "summary": summary,
    }
