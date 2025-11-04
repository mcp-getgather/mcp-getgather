import asyncio
from typing import Annotated, Any

from patchright.async_api import Page

from getgather.actions import handle_network_extraction
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.logs import logger
from getgather.mcp.brand.astro import SpecSchema
from getgather.mcp.dpage import dpage_mcp_tool, dpage_with_action
from getgather.mcp.registry import GatherMCP
from getgather.parse import parse_html

gofood_mcp = GatherMCP(brand_id="gofood", name="Gofood MCP")

@gofood_mcp.tool
async def get_purchase_history() -> dict[str, Any]:
    """Get gofood purchase history."""
    return await dpage_mcp_tool("https://gofood.co.id/en/orders", "gofood_purchase_history")


@gofood_mcp.tool
async def signin() -> dict[str, Any]:
    """Sign in to gofood."""
    return await dpage_mcp_tool("https://gofood.co.id/en/orders", "gofood_purchase_history")


@gofood_mcp.tool
async def get_my_location() -> dict[str, Any] | None:
    """Get gofood my location. After this tool, confirm are the current location is correct or not? If not, use list_locations tool and change_location tool to change the location."""

    async def action(page: Page) -> dict[str, Any]:
        await page.wait_for_selector("input#location-picker")
        await page.wait_for_timeout(2000)
        value = await page.locator("input#location-picker").get_attribute("value")
        placeholder = await page.locator("input#location-picker").get_attribute("placeholder")
        return {"your_current_location": value or placeholder}

    location = await dpage_with_action(
        "https://gofood.co.id/en",
        action,
        _signin_completed=True,
    )

    return {
        "your_current_location": location["your_current_location"] if location else None,
        "system_message": "Ask the user, are the current location is correct or not? If not, use list_locations tool and change_location tool to change the location.",
    }


@gofood_mcp.tool
async def list_locations(
    keyword: Annotated[str, "Keyword to search for locations"],
) -> dict[str, Any] | None:
    """Get gofood locations."""

    if not keyword:
        return {
            "status": "error",
            "error_message": "Keyword is required",
            "system_message": "Ask the user, what is the location keyword to search for?",
        }

    async def action(page: Page) -> dict[str, Any]:
        await page.wait_for_timeout(500)
        await page.click("input#location-picker")
        await page.wait_for_timeout(500)
        await page.fill("input#location-picker", keyword)
        await page.wait_for_timeout(500)
        await page.wait_for_selector("ul[role='listbox']")
        await page.wait_for_timeout(2000)
        locations = await page.locator("ul[role='listbox']").all_text_contents()
        return {"locations": locations}

    return await dpage_with_action(
        "https://gofood.co.id/en",
        action,
        _signin_completed=True,
    )


@gofood_mcp.tool
async def change_location(location_name: str) -> dict[str, Any] | None:
    """Change current location. Get location_name from list_locations tool."""

    async def action(page: Page) -> dict[str, Any]:
        await page.click("input#location-picker")
        await page.fill("input#location-picker", location_name)
        await page.wait_for_selector("ul[role='listbox']")
        await page.click("ul[role='listbox'] li:first-child")
        return {"success": True}

    return await dpage_with_action(
        initial_url=None,
        action=action,
        _signin_completed=True,
    )


@gofood_mcp.tool
async def get_restaurants_near_me(
    keyword: Annotated[
        str,
        "Keyword to search for Restaurants. Optional, if not provided will search near by restaurants",
    ],
) -> dict[str, Any] | None:
    """Get gofood restaurants. You should check get_my_location tool first to confirm the current location. If keyword is provided, will search for restaurants with the keyword."""

    async def action(page: Page) -> dict[str, Any]:
        await page.wait_for_selector("input#location-picker")
        await page.wait_for_timeout(2000)
        value = await page.locator("input#location-picker").get_attribute("value")
        placeholder = await page.locator("input#location-picker").get_attribute("placeholder")

        logger.info("Getting restaurants...")

        if keyword:
            await page.goto(f"https://gofood.co.id/en/search?q={keyword}")
            await page.wait_for_selector('h2:has-text("Matching restos")')
            await page.wait_for_timeout(500)
        else:
            await page.wait_for_selector("button:has-text('Explore')")
            await page.wait_for_timeout(1000)
            await page.click("button:has-text('Explore')")
            await page.wait_for_timeout(1000)
            logger.info("Clicked explore button")
            await page.wait_for_selector('h3:has-text("Our recommendations")')
            logger.info("Waiting for our recommendations")
            await page.goto(f"{page.url}/near_me")
            logger.info("Navigating to near me")
            await page.wait_for_selector('h1:has-text("Near me")')
            logger.info("Waiting for near me")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(300)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(300)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(300)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(300)

        spec_schema = SpecSchema.model_validate({
            "bundle": "search_results.html",
            "format": "html",
            "output": "search_results.json",
            "row_selector": "a[href*='/restaurant/']",
            "extraction_method": "locator",
            "columns": [
                {"name": "name", "selector": "div p"},
                {
                    "name": "url",
                    "selector": "",
                    "attribute": "href",
                },
                {"name": "type", "selector": "div p:nth-of-type(2)"},
                {"name": "distance", "selector": "div[title='Rating'] span"},
                {"name": "rating", "selector": "div.from-gf-background-fill-brand"},
                {"name": "image_url", "selector": "img", "attribute": "src"},
                {"name": "is_closed", "selector": "span:has-text('Closed')"},
            ],
        })

        bundle_result = await parse_html(
            brand_id=BrandIdEnum["amazon"], schema=spec_schema, page=page
        )

        content: list[dict[str, Any]] = []

        for restaurant in bundle_result.content:
            content.append({
                "name": restaurant["name"],
                "url": f"https://gofood.co.id{restaurant['url']}",
                "type": restaurant["type"],
                "distance": restaurant["distance"],
                "rating": restaurant["rating"],
                "image_url": restaurant["image_url"],
            })

        return {"restaurants": content, "location": value or placeholder, "keyword": keyword}

    return await dpage_with_action(
        "https://gofood.co.id/en",
        action,
        _signin_completed=True,
    )


@gofood_mcp.tool
async def get_restaurant_menus(restaurant_url: str | list[str]) -> dict[str, Any] | None:
    """Get gofood restaurant menus. Get restaurant_url from get_restaurants tool. restaurant_url can be a single URL or a list of URLs."""

    async def action(page: Page) -> dict[str, Any]:
        restaurant_urls = [restaurant_url] if isinstance(restaurant_url, str) else restaurant_url

        async def search_single_product(kw: str):
            new_page = await page.context.new_page()
            await new_page.goto(kw)
            await new_page.wait_for_selector("div[id*='section-']")
            await new_page.wait_for_timeout(1000)

            data: list[dict[str, Any]] = []
            lc_rows = new_page.locator("div[id*='section-']")
            for lc in await lc_rows.all():
                section_header = await lc.locator("h2").text_content()
                html = await lc.inner_html()

                logger.info(f"Parsing restaurant menu for {section_header}")
                logger.info(f"HTML: {html}")
                spec_schema = SpecSchema.model_validate({
                    "bundle": f"restaurant_menu_{section_header}.html",
                    "format": "html",
                    "output": f"restaurant_menu_{section_header}.json",
                    "row_selector": "div.overflow-hidden",
                    "extraction_method": "locator",
                    "columns": [
                        {"name": "name", "selector": "h3"},
                        {"name": "description", "selector": "h3 + p"},
                        {"name": "price", "selector": "div > div > span"},
                        {"name": "image_url", "selector": "img", "attribute": "src"},
                        {"name": "is_out_of_stock", "selector": "span:has-text('Out of stock')"},
                    ],
                })

                bundle_result = await parse_html(
                    brand_id=BrandIdEnum["amazon"], schema=spec_schema, html_content=html
                )

                data.append({"content": bundle_result.content, "section_name": section_header})

            return {"restaurant_menu": data, "restaurant_url": kw}

        results_list = await asyncio.gather(*[
            search_single_product(restaurant_url) for restaurant_url in restaurant_urls
        ])

        return {"restaurant_menus": results_list}

    return await dpage_with_action(
        initial_url=None,
        action=action,
        _signin_completed=True,
    )


@gofood_mcp.tool
async def add_or_edit_item_to_cart(
    restaurant_url: Annotated[str, "Restaurant URL. Required."],
    menu_name: str,
    expected_quantity: int = 1,
) -> dict[str, Any] | None:
    """Add item to cart. Get menu_name from get_restaurant_menus tool."""

    async def action(page: Page) -> dict[str, Any]:
        logger.info(f"Adding {menu_name} to cart")

        await page.reload()
        await page.wait_for_timeout(300)

        login_button_exists = await page.locator("a:has-text('Log in')").is_visible()

        if login_button_exists:
            return {
                "system_message": "User is not signed in, please sign in first by calling signin tool. After the sign in is completed, call this tool again."
            }

        await page.goto(restaurant_url)
        await page.wait_for_timeout(300)
        card_locator = page.locator(f"h3:has-text('{menu_name}')").first
        logger.info(f"Card locator: {card_locator}")
        logger.info(f"Card locator count: {await card_locator.count()}")
        logger.info(f"Card locator inner text: {await card_locator.inner_text()}")
        parent_locator = card_locator.locator("../../..")
        parent_inner_text = await parent_locator.inner_text()
        logger.info(f"Parent locator inner text: {parent_inner_text}")
        if "Add" in parent_inner_text:
            button_locator = parent_locator.locator("button")
            logger.info(f"Button locator: {button_locator}")
            logger.info(f"Button locator inner text: {await button_locator.inner_text()}")
            await button_locator.click()

            await page.wait_for_timeout(300)
            is_show_popup = await page.locator("button:has-text('Sure, go ahead')").is_visible()
            if is_show_popup:
                await page.locator("button:has-text('Sure, go ahead')").click()
                await page.wait_for_timeout(300)
            #     if menu_selections:
            #         for menu_selection in menu_selections:
            #             await page.locator("h3:has-text('Customize the dish') + div").locator("span:has-text('menu_selection')").click()
            #             await page.wait_for_timeout(300)
            #         await page.locator("button:has-text('Add to cart - ')").click()
            #         await page.wait_for_timeout(300)
            #         is_popup_confirm = await page.locator("button:has-text('Sure, go ahead')").is_visible()
            #         if is_popup_confirm:
            #             await page.locator("button:has-text('Sure, go ahead')").click()
            #             await page.wait_for_timeout(300)
            #     else:
            #         menu_selection = await page.locator("h3:has-text('Customize the dish') + div").inner_html()
            #         return {"menu_selection": menu_selection, "system_message": "Ask the user, what is the menu selection for the dish."}

        elif "Notes" in parent_inner_text:
            current_qty = (
                await parent_locator.locator("[data-testid='stepper-step']").text_content() or "0"
            )
            current_qty = int(current_qty)
            if current_qty > expected_quantity:
                for _ in range(current_qty - expected_quantity):
                    button_locator = parent_locator.locator(
                        "button[data-testid='stepper-subtract']"
                    )
                    await button_locator.click()
                    await page.wait_for_timeout(300)
            elif current_qty < expected_quantity:
                for _ in range(expected_quantity - current_qty):
                    button_locator = parent_locator.locator("button[data-testid='stepper-add']")
                    await button_locator.click()
                    await page.wait_for_timeout(300)

        await page.wait_for_timeout(300)

        new_page = await page.context.new_page()
        asyncio.create_task(new_page.goto("https://gofood.co.id/en/checkout"))

        cart = await handle_network_extraction(new_page, "api/pricing/estimate")
        cart_items = cart.get("cart")

        logger.info(f"Cart: {cart_items}")
        await new_page.close()

        return {"cart_items": cart_items}

    return await dpage_with_action(
        initial_url=None,
        action=action,
    )


@gofood_mcp.tool
async def cart_summary() -> dict[str, Any] | None:
    """Get cart summary."""

    async def action(page: Page) -> dict[str, Any]:
        new_page = await page.context.new_page()
        asyncio.create_task(new_page.goto("https://gofood.co.id/en/checkout"))

        cart = await handle_network_extraction(new_page, "api/pricing/estimate")
        restaurant_href = await new_page.locator("a:has-text('Add more')").get_attribute("href")
        restaurant_url = f"https://gofood.co.id{restaurant_href}"

        address_html = (
            await new_page.locator("label:has-text('Address detail')").locator("../..").inner_html()
        )

        await new_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await new_page.wait_for_timeout(300)
        await new_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await new_page.wait_for_timeout(300)

        can_apply_promo = await new_page.locator("button:has-text('Apply')").is_visible()
        if can_apply_promo:
            await new_page.locator("button:has-text('Apply')").click()
            await new_page.wait_for_timeout(300)
            asyncio.create_task(new_page.reload())

            cart = await handle_network_extraction(new_page, "api/pricing/estimate")
        await new_page.close()

        return {
            "cart_summary": cart,
            "restaurant_url": restaurant_url,
            "address_html": address_html,
        }

    return await dpage_with_action(
        initial_url=None,
        action=action,
    )


@gofood_mcp.tool
async def checkout() -> dict[str, Any] | None:
    """Checkout order."""

    async def action(page: Page) -> dict[str, Any]:
        new_page = await page.context.new_page()
        await new_page.set_viewport_size({"height": 812, "width": 375})
        await new_page.wait_for_timeout(300)
        await new_page.goto("https://gofood.co.id/en/checkout")
        await new_page.wait_for_timeout(300)

        await new_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await new_page.wait_for_timeout(300)
        await new_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await new_page.wait_for_timeout(300)

        await new_page.locator("button:has-text('GoFood now')").click()
        await new_page.wait_for_timeout(300)
        await new_page.locator("div[id*='headlessui-dialog-panel']").wait_for(state="visible")
        await new_page.wait_for_timeout(300)
        await new_page.locator(
            "div[id*='headlessui-dialog-panel'] button:has-text('GoFood now')"
        ).click()
        await new_page.wait_for_timeout(2000)
        await new_page.wait_for_selector("div:has-text('Delivery in')")
        html = await new_page.locator(
            "div#__next > div > div:nth-of-type(2) > div:nth-of-type(2)"
        ).inner_html()
        await new_page.close()

        return {"message": "Checkout success", "detail": html, "order_url": new_page.url}

    return await dpage_with_action(
        initial_url=None,
        action=action,
    )


@gofood_mcp.tool
async def get_ongoing_order_details() -> dict[str, Any] | None:
    """Get ongoing gofood order details from latest checkout/orders."""

    async def action(page: Page) -> dict[str, Any]:
        await page.locator("a:has-text('Track purchase')").click()
        await page.wait_for_selector("div:has-text('Delivery in')")
        html = await page.locator(
            "div#__next > div > div:nth-of-type(2) > div:nth-of-type(2)"
        ).inner_html()
        return {"message": "Order details", "detail": html}

    return await dpage_with_action(initial_url="https://gofood.co.id/en/orders", action=action)
