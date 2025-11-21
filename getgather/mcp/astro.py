from typing import Any
from urllib.parse import quote

from patchright.async_api import Page

from getgather.browser.profile import BrowserProfile
from getgather.mcp.dpage import dpage_mcp_tool, dpage_with_action
from getgather.mcp.registry import GatherMCP

astro_mcp = GatherMCP(brand_id="astro", name="Astro MCP")


@astro_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get astro purchase history using distillation."""
    return await dpage_mcp_tool("https://www.astronauts.id/order/history", "astro_purchase_history")


@astro_mcp.tool
async def search_product(keyword: str) -> dict[str, Any]:
    """Search product on astro."""
    encoded_keyword = quote(keyword)

    return await dpage_mcp_tool(
        f"https://www.astronauts.id/search?q={encoded_keyword}", "astro_search_product"
    )


@astro_mcp.tool
async def get_product_details(product_url: str) -> dict[str, Any]:
    """Get product detail from astro. Get product_url from search_product tool."""
    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    return await dpage_mcp_tool(full_url, "astro_product_detail")


@astro_mcp.tool
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from astro."""
    return await dpage_mcp_tool("https://www.astronauts.id/cart", "astro_cart")


@astro_mcp.tool
async def add_item_to_cart(product_url: str) -> dict[str, Any]:
    """Add item to cart on astro (add new item or update existing quantity). Get product_url from search_product tool."""
    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    async def action(page: Page, _: BrowserProfile) -> dict[str, Any]:
        # Wait for page to be ready
        main_element = page.locator("main")
        await main_element.is_visible(timeout=5000)

        cart_button = page.locator('button[data-testid="pdp-atc-btn"]')
        await cart_button.click()

        # Click needs sometime to finish
        await page.wait_for_timeout(2000)

        return {"added_to_cart": {"product_url": product_url}}

    return await dpage_with_action(action=action, initial_url=full_url)


@astro_mcp.tool
async def update_cart_quantity(product_name: str, quantity: int) -> dict[str, Any]:
    """Update cart item quantity on astro (set quantity to 0 to remove item). Use product name from cart summary."""

    async def action(page: Page, browser_profile: BrowserProfile) -> dict[str, Any]:
        await page.wait_for_selector("main.MuiBox-root")

        product_name_item = page.locator(f"span:has-text('{product_name}')")

        if not await product_name_item.is_visible():
            return {
                "success": False,
                "message": f"Product '{product_name}' not found in cart",
                "product_name": product_name,
                "action": "update_failed",
            }

        # Find the container that has the quantity controls
        item = product_name_item.locator("xpath=../..")

        # Get current quantity
        quantity_element = item.locator("span.MuiTypography-body-small")
        current_quantity_text = await quantity_element.text_content()
        if not current_quantity_text:
            return {
                "success": False,
                "message": f"Cannot find current quantity",
                "product_name": product_name,
                "action": "update_failed",
            }

        current_quantity = int(current_quantity_text.strip())

        # Calculate how many clicks we need
        clicks_needed = quantity - current_quantity

        if clicks_needed == 0:
            return {"product_name": product_name, "quantity": quantity, "action": "no_change"}

        # Find the button container
        button_container = item.locator("div.MuiBox-root.css-1aek3i0")

        if clicks_needed > 0:
            # Click increment button (plus button - last div)
            increment_button = button_container.locator("div.MuiBox-root.css-70qvj9").nth(1)
            for _ in range(clicks_needed):
                await increment_button.click()
                await page.wait_for_timeout(300)  # Small delay between clicks
        else:
            # Click decrement button (minus button - first div)
            decrement_button = button_container.locator("div.MuiBox-root.css-70qvj9").nth(0)
            for _ in range(abs(clicks_needed)):
                await decrement_button.click()
                await page.wait_for_timeout(300)  # Small delay between clicks

        # Wait a bit for the final update to process
        await page.wait_for_timeout(500)

        # Get final quantity (if item still exists)
        if quantity == 0:
            # Item should be removed
            return {"product_name": product_name, "quantity": 0, "action": "removed"}
        else:
            final_quantity_text = await quantity_element.text_content()
            final_quantity = int(final_quantity_text.strip()) if final_quantity_text else 0
            return {"product_name": product_name, "quantity": final_quantity, "action": "updated"}

    return await dpage_with_action(action=action, initial_url="https://www.astronauts.id/cart")
