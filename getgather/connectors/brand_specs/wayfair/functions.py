import json
from typing import Any

from patchright.async_api import Page
from rich.markup import escape

from getgather.logs import logger


async def retrieve_image_url_and_price_for_wayfair(
    page: Page,
    content: str,
) -> dict[str, Any]:
    """Retrieve the image URL from the page."""
    logger.info(f"🔍 Retrieving image URLs")
    temp_content = json.loads(content)

    nodes = temp_content.get("data", {}).get("orderProductPagesByCustomer", {}).get("nodes", [])

    if not nodes or not isinstance(nodes, list):
        return temp_content

    try:
        url = (
            temp_content.get("data", {})
            .get("orderProductPagesByCustomer", {})
            .get("nodes", [])[0]
            .get("product", {})
            .get("productWebsiteUrl", "")
        )
        if not url:
            return temp_content
        logger.debug(f"🔍 URL: {url}")
        await page.goto(url)
        product_name = (
            temp_content.get("data", {})
            .get("orderProductPagesByCustomer", {})
            .get("nodes", [])[0]
            .get("product", {})
            .get("productName", "")[:10]
        )
        logger.debug(
            f"🔍 Product name: {escape(product_name)}"
        )  # Use escape to render [] characters in strings

        selector_for_image = f"img[alt*={json.dumps(product_name)}]"

        if selector_for_image:
            logger.debug(f"🔍 Retrieving image URL for selector: {escape(selector_for_image)}")
            image_url = await page.locator(selector_for_image).first.get_attribute("src")
            temp_content["data"]["orderProductPagesByCustomer"]["nodes"][0]["product"][
                "imageUrl"
            ] = image_url

        price_selector = "span[data-name-id='PriceDisplay']"
        logger.debug(f"🔍 Retrieving price for selector: {escape(price_selector)}")
        price = await page.locator(price_selector).first.text_content()
        temp_content["data"]["orderProductPagesByCustomer"]["nodes"][0]["product"]["price"] = price
    except Exception as e:
        logger.error(f"❌ Error retrieving image URL and price for Wayfair: {e}")
        return temp_content
    return temp_content
