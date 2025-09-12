from typing import Any

from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import get_global_browser_session, with_global_browser_session
from getgather.parse import parse_html

amain_mcp = BrandMCPBase(brand_id="amain", name="Amain MCP")


@amain_mcp.tool(tags={"private"})
@with_global_browser_session
async def get_cart() -> dict[str, Any]:
    """Get cart of amain."""

    browser_session = get_global_browser_session()
    page = await browser_session.page()

    await page.goto(f"https://www.amainhobbies.com/shopping-cart")
    await page.wait_for_selector("div.product-list")
    await page.wait_for_timeout(1000)
    html = await page.locator("div.product-list").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div.product",
        "columns": [
            {"name": "description", "selector": "div.description"},
            {"name": "qty", "selector": "div.quantity"},
            {"name": "total_price", "selector": "div.total"},
        ],
    })
    result = await parse_html(brand_id=amain_mcp.brand_id, html_content=html, schema=spec_schema)
    return {"cart_data": result.content}
