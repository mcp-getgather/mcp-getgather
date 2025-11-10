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

    # html = await page.locator("div[data-testid='srp-main']").inner_html()
    #
    # spec_schema = SpecSchema.model_validate({
    #     "bundle": "",
    #     "format": "html",
    #     "output": "",
    #     "row_selector": "div.MuiGrid-item.MuiGrid-grid-xs-4.css-qdep8d",
    #     "columns": [
    #         {"name": "product_name", "selector": "span.MuiTypography-paragraph-tiny.css-xkitcr"},
    #         {"name": "product_url", "selector": "a[href^='/p/']", "attribute": "href"},
    #         {"name": "price", "selector": "span.MuiTypography-body-smallStrong.css-e2mums"},
    #         {"name": "product_size", "selector": "span.MuiTypography-caption-tiny.css-1mxh19w"},
    #         {
    #             "name": "product_image",
    #             "selector": "img.image[src*='image.astronauts.cloud']",
    #             "attribute": "src",
    #         },
    #         {
    #             "name": "discount_percentage",
    #             "selector": "span.MuiTypography-caption-tinyBold.css-1xzi4v7",
    #         },
    #         {
    #             "name": "original_price",
    #             "selector": "span.MuiTypography-caption-tiny.css-1mxh19w[style*='line-through']",
    #         },
    #         {"name": "stock_status", "selector": "span.MuiTypography-caption-tiny.css-1lb2yr7"},
    #     ],
    # })
    # result = await parse_html(brand_id=astro_mcp.brand_id, html_content=html, schema=spec_schema)
    # return {"product_list": result.content}
