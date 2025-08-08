import json
from typing import Any

from patchright.async_api import Page

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

    image_selector = "img[alt*='{product_name}']"
    price_selector = "span[data-name-id='PriceDisplay']"

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
        await page.goto(url)

        image_selector = image_selector.format(
            product_name=temp_content.get("data", {})
            .get("orderProductPagesByCustomer", {})
            .get("nodes", [])[0]
            .get("product", {})
            .get("productName", "")[:10]
        )
        if image_selector:
            logger.debug(f"🔍 Retrieving image URL for selector: {image_selector}")
            image_url = await page.locator(image_selector).get_attribute("src")
            temp_content["data"]["orderProductPagesByCustomer"]["nodes"][0]["product"][
                "imageUrl"
            ] = image_url
        logger.debug(f"🔍 Retrieving price for selector: {price_selector}")
        price = await page.locator(price_selector).text_content()
        temp_content["data"]["orderProductPagesByCustomer"]["nodes"][0]["product"]["price"] = price
    except Exception as e:
        logger.error(f"❌ Error retrieving image URL and price for Wayfair: {e}")
        return temp_content
    return temp_content
