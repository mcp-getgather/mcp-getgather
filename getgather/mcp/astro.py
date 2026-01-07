import asyncio
from typing import Any
from urllib.parse import quote

import zendriver as zd

from getgather.mcp.dpage import zen_dpage_mcp_tool, zen_dpage_with_action
from getgather.mcp.registry import GatherMCP
from getgather.zen_distill import page_query_selector

astro_mcp = GatherMCP(brand_id="astro", name="Astro MCP")


@astro_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get astro purchase history using distillation."""
    return await zen_dpage_mcp_tool(
        "https://www.astronauts.id/order/history", "astro_purchase_history"
    )


@astro_mcp.tool
async def search_product(keyword: str) -> dict[str, Any]:
    """Search product on astro."""
    encoded_keyword = quote(keyword)

    return await zen_dpage_mcp_tool(
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

    return await zen_dpage_mcp_tool(full_url, "astro_product_detail")


@astro_mcp.tool
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from astro."""
    return await zen_dpage_mcp_tool("https://www.astronauts.id/cart", "astro_cart")


@astro_mcp.tool
async def add_item_to_cart(product_url: str) -> dict[str, Any]:
    """Add item to cart on astro (add new item or update existing quantity). Get product_url from search_product tool."""
    # Ensure the product URL is a full URL
    if product_url.startswith("/p/"):
        full_url = f"https://www.astronauts.id{product_url}"
    else:
        full_url = product_url

    async def action(page: zd.Tab, browser: zd.Browser) -> dict[str, Any]:
        # Wait for page to be ready
        main_element = await page_query_selector(page, "main")
        if not main_element:
            return {"error": "Page failed to load"}

        cart_button = await page_query_selector(page, 'button[data-testid="pdp-atc-btn"]')
        if cart_button:
            await cart_button.click()

        # Click needs sometime to finish
        await asyncio.sleep(2)

        return {"added_to_cart": {"product_url": product_url}}

    return await zen_dpage_with_action(initial_url=full_url, action=action)


@astro_mcp.tool
async def update_cart_quantity(product_name: str, quantity: int) -> dict[str, Any]:
    """Update cart item quantity on astro (set quantity to 0 to remove item). Use product name from cart summary."""

    async def action(page: zd.Tab, browser: zd.Browser) -> dict[str, Any]:
        # Wait for page to be ready
        main_element = await page_query_selector(page, "main.MuiBox-root")
        if not main_element:
            await asyncio.sleep(2)  # Give it more time to load
            main_element = await page_query_selector(page, "main.MuiBox-root")
            if not main_element:
                return {"error": "Cart page failed to load"}

        # Use JavaScript to find and interact with cart items
        escaped_name = product_name.replace("'", "\\'").replace('"', '\\"')

        # Find the product and get current quantity
        find_product_js = f"""
            (() => {{
                const spans = document.querySelectorAll('span');
                for (const span of spans) {{
                    if (span.textContent && span.textContent.includes('{escaped_name}')) {{
                        // Navigate up to find the container with quantity controls
                        let container = span.parentElement?.parentElement;
                        if (!container) return null;

                        // Find quantity display
                        const quantitySpan = container.querySelector('span.MuiTypography-body-small');
                        if (!quantitySpan) return null;

                        return {{
                            found: true,
                            currentQuantity: parseInt(quantitySpan.textContent?.trim() || '0', 10)
                        }};
                    }}
                }}
                return null;
            }})()
        """

        result = await page.evaluate(find_product_js)
        if not result:
            return {
                "success": False,
                "message": f"Product '{product_name}' not found in cart",
                "product_name": product_name,
                "action": "update_failed",
            }

        current_quantity = int(result.get("currentQuantity", 0))  # type: ignore[union-attr]
        clicks_needed = quantity - current_quantity

        if clicks_needed == 0:
            return {"product_name": product_name, "quantity": quantity, "action": "no_change"}

        # Click increment or decrement buttons
        button_index = 1 if clicks_needed > 0 else 0  # 1 for increment, 0 for decrement
        click_count: int = abs(clicks_needed)

        for _ in range(click_count):
            click_button_js = f"""
                (() => {{
                    const spans = document.querySelectorAll('span');
                    for (const span of spans) {{
                        if (span.textContent && span.textContent.includes('{escaped_name}')) {{
                            let container = span.parentElement?.parentElement;
                            if (!container) return false;

                            const buttonContainer = container.querySelector('div.MuiBox-root.css-1aek3i0');
                            if (!buttonContainer) return false;

                            const buttons = buttonContainer.querySelectorAll('div.MuiBox-root.css-70qvj9');
                            if (buttons.length > {button_index}) {{
                                buttons[{button_index}].click();
                                return true;
                            }}
                            return false;
                        }}
                    }}
                    return false;
                }})()
            """
            await page.evaluate(click_button_js)
            await asyncio.sleep(0.3)  # Small delay between clicks

        # Wait for the final update to process
        await asyncio.sleep(0.5)

        # Get final quantity (if item still exists)
        if quantity == 0:
            return {"product_name": product_name, "quantity": 0, "action": "removed"}

        # Get updated quantity
        get_quantity_js = f"""
            (() => {{
                const spans = document.querySelectorAll('span');
                for (const span of spans) {{
                    if (span.textContent && span.textContent.includes('{escaped_name}')) {{
                        let container = span.parentElement?.parentElement;
                        if (!container) return 0;
                        const quantitySpan = container.querySelector('span.MuiTypography-body-small');
                        return parseInt(quantitySpan?.textContent?.trim() || '0', 10);
                    }}
                }}
                return 0;
            }})()
        """

        final_quantity = await page.evaluate(get_quantity_js)
        return {"product_name": product_name, "quantity": final_quantity, "action": "updated"}

    return await zen_dpage_with_action(initial_url="https://www.astronauts.id/cart", action=action)
