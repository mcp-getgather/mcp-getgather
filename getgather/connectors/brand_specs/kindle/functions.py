from playwright.async_api import Locator


async def extract_url(locator: Locator) -> str | None:
    """
    Extract the URL from the title locator, whose dom id is in the format
    content-title-<product_id>.
    """
    dom_id = await locator.get_attribute("id")
    if dom_id is None:
        return None
    product_id = dom_id.removeprefix("content-title-")
    return f"https://www.amazon.com/gp/product/{product_id}"
