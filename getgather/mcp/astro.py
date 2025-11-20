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
    print(f"DEBUGPRINT[44]: astro.py:73: product_name={product_name}")
    """Update cart item quantity on astro (set quantity to 0 to remove item). Use product name from cart summary."""

    async def action(page: Page, _: BrowserProfile) -> dict[str, Any]:
        await page.wait_for_selector("main.MuiBox-root")

        product_name_item = page.locator(f"span:has-text('{product_name}')")

        if not await product_name_item.is_visible():
            return {
                "success": False,
                "message": f"Product '{product_name}' not found in cart",
                "product_name": product_name,
                "action": "update_failed",
            }

        item = product_name_item.locator("xpath=../..")

        quantity_element = item.locator("span.MuiTypography-body-small")

        # Set the text content of the element
        await quantity_element.evaluate(f"el => el.textContent = '{quantity}'")

        final_quantity = await quantity_element.text_content()

        return {"product_name": product_name, "quantity": final_quantity}

    return await dpage_with_action(action=action, initial_url="https://www.astronauts.id/cart")
