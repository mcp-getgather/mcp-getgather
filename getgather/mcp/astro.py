from typing import Any
from urllib.parse import quote

from patchright.async_api import Page

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
async def add_item_to_cart(product_url: str, quantity: int = 1) -> dict[str, Any]:
    """Add item to cart on astro (add new item or update existing quantity). Get product_url from search_product tool."""
    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    async def action(page: Page) -> dict[str, Any]:
        cart_button = page.locator("button:has-text('Keranjang')")
        await cart_button.wait_for(state="visible", timeout=5000)

        print(
            f"DEBUGPRINT[42]: astro.py:56: is_cart_button_enable={await cart_button.is_visible()}"
        )

        return {"added_to_cart": {"product_url": product_url, "quantity": quantity}}

    return await dpage_with_action(initial_url=full_url, action=action)

    # # Check if quantity controls already exist (item already in cart) - only in main product section
    # main_product_section = page.locator("div.MuiBox-root.css-19midj6")
    # quantity_controls = main_product_section.locator("div.MuiBox-root.css-1aek3i0")
    # is_already_in_cart = await quantity_controls.is_visible()
    #
    # if is_already_in_cart:
    #     current_quantity_element = quantity_controls.locator("span.MuiTypography-body-small")
    #     current_quantity_text = await current_quantity_element.text_content()
    #     current_quantity = int(current_quantity_text or "0")
    #
    #     final_quantity, adjustment_succeeded = await _adjust_quantity_with_detection(
    #         quantity_controls, quantity, current_quantity, page, "product"
    #     )
    #
    #     # Wait for backend API call to complete before closing browser
    #     await page.wait_for_timeout(1000)
    #
    #     return _format_quantity_result(
    #         quantity,
    #         current_quantity,
    #         final_quantity,
    #         adjustment_succeeded,
    #         full_url,
    #         "",
    #         "product",
    #     )
    # else:
    #     # Item not in cart, check if add to cart button exists - only in main product section
    #     add_to_cart_button = main_product_section.locator("button[data-testid='pdp-atc-btn']")
    #     if not await add_to_cart_button.is_visible():
    #         return {
    #             "success": False,
    #             "error": "Add to cart button not found or product not available",
    #         }
    #
    #     await add_to_cart_button.click()
    #     await page.wait_for_timeout(300)
    #
    #     await quantity_controls.wait_for(state="visible", timeout=5000)
    #
    #     final_quantity, adjustment_succeeded = await _adjust_quantity_with_detection(
    #         quantity_controls, quantity, 1, page, "product"
    #     )
    #
    #     # Wait for backend API call to complete before closing browser
    #     await page.wait_for_timeout(1000)
    #
    #     return _format_quantity_result(
    #         quantity, 0, final_quantity, adjustment_succeeded, full_url, "", "product"
    #     )
