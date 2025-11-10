from typing import Any
from urllib.parse import quote

from getgather.mcp.dpage import dpage_mcp_tool
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

    # spec_schema = SpecSchema.model_validate({
    #     "bundle": "",
    #     "format": "html",
    #     "output": "",
    #     "row_selector": "main.MuiBox-root",
    #     "columns": [
    #         {"name": "product_title", "selector": "h1[data-testid='pdp-title']"},
    #         {"name": "price", "selector": "p[data-testid='pdp-price']"},
    #         {"name": "description", "selector": "span[data-testid='pdp-description-content']"},
    #         {
    #             "name": "expiry_date",
    #             "selector": "div[data-testid='pdp-expiry-section'] span.MuiTypography-caption-small",
    #         },
    #         {
    #             "name": "return_condition",
    #             "selector": "div[data-testid='pdp-retur-message'] span.MuiTypography-caption-small",
    #         },
    #         {"name": "product_image", "selector": "img.image", "attribute": "src"},
    #         {"name": "add_to_cart_available", "selector": "button[data-testid='pdp-atc-btn']"},
    #     ],
    # })
    # result = await parse_html(brand_id=astro_mcp.brand_id, html_content=html, schema=spec_schema)
    #
    # product_details: dict[str, Any] = (
    #     result.content[0] if result.content and len(result.content) > 0 else {}
    # )
    #
    # return {"product_details": product_details}
