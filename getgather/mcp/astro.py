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

    return await dpage_with_action(initial_url=full_url, action=action)
