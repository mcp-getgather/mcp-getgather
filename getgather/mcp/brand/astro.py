from typing import Any, cast

from patchright.async_api import Locator, Page

from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import (
    get_mcp_browser_session,
    with_brand_browser_session,
)
from getgather.parse import parse_html

astro_mcp = BrandMCPBase(brand_id="astro", name="Astro MCP")


async def _adjust_quantity_with_detection(
    quantity_controls: Locator,
    target_quantity: int,
    current_quantity: int,
    page: Page,
    context: str = "product",  # "product" or "cart"
) -> tuple[int, bool]:
    """Shared quantity adjustment logic with change detection and edge case handling.

    Args:
        quantity_controls: The quantity control container
        target_quantity: Desired quantity (0 = remove)
        current_quantity: Current quantity
        page: Page object
        context: "product" or "cart" for different edge case handling

    Returns:
        tuple[final_quantity, adjustment_succeeded]
    """
    quantity_diff = target_quantity - current_quantity

    if quantity_diff == 0:
        return current_quantity, True

    # Get buttons
    plus_button = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(1)
    minus_button = quantity_controls.locator("div.MuiBox-root.css-70qvj9").nth(0)
    current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")

    # Adjust quantity step by step with detection
    steps_needed = abs(quantity_diff)
    button = plus_button if quantity_diff > 0 else minus_button

    for _ in range(steps_needed):
        prev_qty_text = await current_quantity_element.text_content()
        prev_qty = int(prev_qty_text or str(current_quantity))

        await button.click()

        # Wait for quantity change with timeout
        change_detected = False
        for _ in range(10):  # Max 5 seconds
            await page.wait_for_timeout(500)

            # Handle edge case: quantity 0 might make element disappear
            try:
                new_qty_text = await current_quantity_element.text_content()
                new_qty = int(new_qty_text or "0")

                # Check if change occurred in expected direction
                if (quantity_diff > 0 and new_qty > prev_qty) or (
                    quantity_diff < 0 and new_qty < prev_qty
                ):
                    change_detected = True
                    current_quantity = new_qty
                    break

            except Exception:
                # Element might have disappeared (quantity → 0 in cart)
                if target_quantity == 0 and context == "cart":
                    return 0, True  # Success: item removed from cart
                # For product page, check if "Keranjang" button appeared
                elif target_quantity == 0 and context == "product":
                    try:
                        keranjang_btn = page.locator("button[data-testid='pdp-atc-btn']")
                        if await keranjang_btn.is_visible():
                            return 0, True  # Success: reverted to add-to-cart state
                    except:
                        pass
                break

        if not change_detected:
            # Hit a limit (stock or minimum), return current state
            try:
                final_qty_text = await current_quantity_element.text_content()
                return int(final_qty_text or str(current_quantity)), False
            except:
                # Element disappeared but target wasn't 0
                return 0, target_quantity == 0

    # Get final quantity
    try:
        final_qty_text = await current_quantity_element.text_content()
        final_quantity = int(final_qty_text or "0")
    except:
        # Element disappeared
        final_quantity = 0

    return final_quantity, True


def _format_quantity_result(
    target_quantity: int,
    current_quantity: int,
    final_quantity: int,
    adjustment_succeeded: bool,
    product_url: str = "",
    product_name: str = "",
    context: str = "product",
) -> dict[str, Any]:
    """Format the result of quantity adjustment with stock limit detection."""
    quantity_changed = final_quantity - current_quantity

    # Check if target was reached (stock limit detection)
    if target_quantity > 0 and final_quantity < target_quantity:
        return {
            "success": False,
            "message": f"Stock limit reached: only {final_quantity} available (requested {target_quantity})",
            "previous_quantity": current_quantity,
            "final_quantity": final_quantity,
            "quantity_changed": quantity_changed,
            **({"product_url": product_url} if product_url else {}),
            **({"product_name": product_name} if product_name else {}),
            "action": "stock_limit_reached",
            "available_stock": final_quantity,
            "requested_quantity": target_quantity,
        }

    # Success cases
    if context == "product":
        if current_quantity == 0:
            action = "added_to_cart"
            message = f"Successfully added {final_quantity} item(s) to cart"
        else:
            action = "quantity_updated"
            message = f"Updated quantity from {current_quantity} to {final_quantity} item(s)"
    else:  # cart context
        if target_quantity == 0:
            action = "removed_from_cart"
            message = f"Removed '{product_name}' from cart"
        else:
            action = "quantity_updated"
            message = (
                f"Updated '{product_name}' quantity from {current_quantity} to {final_quantity}"
            )

    return {
        "success": True,
        "message": message,
        "previous_quantity": current_quantity,
        "final_quantity": final_quantity,
        "quantity_changed": quantity_changed,
        **({"product_url": product_url} if product_url else {}),
        **({"product_name": product_name} if product_name else {}),
        "action": action,
    }


@astro_mcp.tool(tags={"private"})
@with_brand_browser_session
async def add_item_to_cart(product_url: str, quantity: int = 1) -> dict[str, Any]:
    """Add item to cart on astro (add new item or update existing quantity). Get product_url from search_product tool."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()

    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    await page.goto(full_url, wait_until="commit")
    await page.goto(full_url, wait_until="commit")
    await page.wait_for_selector("main.MuiBox-root")
    await page.wait_for_timeout(1000)

    # Check if quantity controls already exist (item already in cart) - only in main product section
    main_product_section = page.locator("div.MuiBox-root.css-19midj6")
    quantity_controls = main_product_section.locator("div.MuiBox-root.css-1aek3i0")
    is_already_in_cart = await quantity_controls.is_visible()

    if is_already_in_cart:
        current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")
        current_quantity_text = await current_quantity_element.text_content()
        current_quantity = int(current_quantity_text or "0")

        final_quantity, adjustment_succeeded = await _adjust_quantity_with_detection(
            quantity_controls, quantity, current_quantity, page, "product"
        )

        # Wait for backend API call to complete before closing browser
        await page.wait_for_timeout(1000)

        return _format_quantity_result(
            quantity,
            current_quantity,
            final_quantity,
            adjustment_succeeded,
            full_url,
            "",
            "product",
        )
    else:
        # Item not in cart, check if add to cart button exists - only in main product section
        add_to_cart_button = main_product_section.locator("button[data-testid='pdp-atc-btn']")
        if not await add_to_cart_button.is_visible():
            return {
                "success": False,
                "error": "Add to cart button not found or product not available",
            }

        await add_to_cart_button.click()
        await page.wait_for_timeout(300)

        await quantity_controls.wait_for(state="visible", timeout=5000)

        final_quantity, adjustment_succeeded = await _adjust_quantity_with_detection(
            quantity_controls, quantity, 1, page, "product"
        )

        # Wait for backend API call to complete before closing browser
        await page.wait_for_timeout(1000)

        return _format_quantity_result(
            quantity, 0, final_quantity, adjustment_succeeded, full_url, "", "product"
        )


@astro_mcp.tool(tags={"private"})
@with_brand_browser_session
async def update_cart_quantity(product_name: str, quantity: int) -> dict[str, Any]:
    """Update cart item quantity on astro (set quantity to 0 to remove item). Use product name from cart summary."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()

    await page.goto("https://www.astronauts.id/cart", wait_until="commit")
    await page.wait_for_selector("main.MuiBox-root")
    await page.wait_for_timeout(1000)

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

    current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")
    current_quantity_text = await current_quantity_element.text_content()
    current_quantity = int(current_quantity_text or "0")

    final_quantity, adjustment_succeeded = await _adjust_quantity_with_detection(
        quantity_controls, quantity, current_quantity, page, "cart"
    )

    # Wait for update to complete
    await page.wait_for_timeout(1000)

    return _format_quantity_result(
        quantity,
        current_quantity,
        final_quantity,
        adjustment_succeeded,
        "",
        product_name,
        "cart",
    )


@astro_mcp.tool(tags={"private"})
@with_brand_browser_session
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from astro."""
    browser_session = get_mcp_browser_session()
    page = await browser_session.page()

    await page.goto("https://www.astronauts.id/cart", wait_until="commit")
    await page.wait_for_selector("main.MuiBox-root")
    await page.wait_for_timeout(1000)
    html = await page.locator("body").inner_html()

    # Extract available items
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
        brand_id=astro_mcp.brand_id, html_content=html, schema=available_items_schema
    )

    # Extract unavailable items
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
        brand_id=astro_mcp.brand_id, html_content=html, schema=unavailable_items_schema
    )

    # Extract totals
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
        brand_id=astro_mcp.brand_id, html_content=html, schema=summary_schema
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
        brand_id=astro_mcp.brand_id, html_content=html, schema=total_schema
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
