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


@astro_mcp.tool
async def get_cart_summary() -> dict[str, Any]:
    """Get cart summary from astro."""
    return await dpage_mcp_tool("https://www.astronauts.id/cart", "astro_cart")

    # # Extract available items
    # available_items_schema = SpecSchema.model_validate({
    #     "bundle": "",
    #     "format": "html",
    #     "output": "",
    #     "row_selector": "div.MuiBox-root.css-bnftmf div.MuiBox-root.css-1msuw7t",
    #     "columns": [
    #         {
    #             "name": "name",
    #             "selector": "div.MuiBox-root.css-j7qwjs span.MuiTypography-body-default",
    #         },
    #         {"name": "image_url", "selector": "img.MuiBox-root.css-1jmoofa", "attribute": "src"},
    #         {
    #             "name": "quantity",
    #             "selector": "div.MuiBox-root.css-1aek3i0 span.MuiTypography-body-small",
    #         },
    #         {
    #             "name": "current_price",
    #             "selector": "div.MuiBox-root.css-0:last-child p.MuiTypography-body-default.css-133xbhx",
    #         },
    #         {
    #             "name": "original_price",
    #             "selector": "div.MuiBox-root.css-0:last-child span.MuiTypography-body-default.css-1bb6qij",
    #         },
    #         {
    #             "name": "discount_percentage",
    #             "selector": "div.css-6qgay2 span.MuiTypography-caption-tiny",
    #         },
    #     ],
    # })
    #
    # available_items_result = await parse_html(
    #     brand_id=astro_mcp.brand_id, html_content=html, schema=available_items_schema
    # )
    #
    # # Extract unavailable items
    # unavailable_items_schema = SpecSchema.model_validate({
    #     "bundle": "",
    #     "format": "html",
    #     "output": "",
    #     "row_selector": "div.MuiBox-root.css-g89h0y div.MuiBox-root.css-1msuw7t",
    #     "columns": [
    #         {
    #             "name": "name",
    #             "selector": "div.MuiBox-root.css-j7qwjs span.MuiTypography-body-default",
    #         },
    #         {"name": "image_url", "selector": "img.MuiBox-root.css-1jmoofa", "attribute": "src"},
    #         {
    #             "name": "quantity",
    #             "selector": "div.MuiBox-root.css-1bmdty span.MuiTypography-body-small",
    #         },
    #     ],
    # })
    #
    # unavailable_items_result = await parse_html(
    #     brand_id=astro_mcp.brand_id, html_content=html, schema=unavailable_items_schema
    # )
    #
    # # Extract totals
    # summary_schema = SpecSchema.model_validate({
    #     "bundle": "",
    #     "format": "html",
    #     "output": "",
    #     "row_selector": "div.MuiBox-root.css-4kor8h",
    #     "columns": [
    #         {
    #             "name": "subtotal",
    #             "selector": "div.MuiBox-root.css-1duxxgg:first-child span:last-child",
    #         },
    #         {
    #             "name": "shipping_fee",
    #             "selector": "div.MuiBox-root.css-1duxxgg:nth-child(2) div.MuiBox-root.css-171onha:last-child span:last-child",
    #         },
    #         {
    #             "name": "service_fee",
    #             "selector": "div.MuiBox-root.css-1duxxgg:last-child span:last-child",
    #         },
    #     ],
    # })
    #
    # summary_result = await parse_html(
    #     brand_id=astro_mcp.brand_id, html_content=html, schema=summary_schema
    # )
    #
    # # Extract final total
    # total_schema = SpecSchema.model_validate({
    #     "bundle": "",
    #     "format": "html",
    #     "output": "",
    #     "row_selector": "div.MuiBox-root.css-1ia6xgx",
    #     "columns": [
    #         {
    #             "name": "total_amount",
    #             "selector": "div.MuiBox-root.css-axw7ok span.MuiTypography-body-default.css-g3g47m",
    #         },
    #         {"name": "savings", "selector": "div.css-n6k44k span.MuiTypography-caption-tinyBold"},
    #     ],
    # })
    #
    # total_result = await parse_html(
    #     brand_id=astro_mcp.brand_id, html_content=html, schema=total_schema
    # )
    #
    # # Process available items
    # available_items: list[dict[str, Any]] = []
    # available_content: list[Any] = available_items_result.content or []
    # for item in available_content:
    #     if not isinstance(item, dict):
    #         continue
    #     item_dict: dict[str, Any] = cast(dict[str, Any], item)
    #     available_items.append({
    #         "name": item_dict.get("name", ""),
    #         "quantity": int(item_dict.get("quantity", "1")),
    #         "price": item_dict.get("current_price", ""),
    #         "original_price": item_dict.get("original_price"),
    #         "image_url": item_dict.get("image_url", ""),
    #         "status": "available",
    #         "discount_percentage": item_dict.get("discount_percentage", "0%"),
    #     })
    #
    # # Process unavailable items
    # unavailable_items: list[dict[str, Any]] = []
    # unavailable_content: list[Any] = unavailable_items_result.content or []
    # for item in unavailable_content:
    #     if not isinstance(item, dict):
    #         continue
    #     unavail_item_dict: dict[str, Any] = cast(dict[str, Any], item)
    #     unavailable_items.append({
    #         "name": unavail_item_dict.get("name", ""),
    #         "quantity": int(unavail_item_dict.get("quantity", "1")),
    #         "image_url": unavail_item_dict.get("image_url", ""),
    #         "status": "unavailable",
    #         "reason": "Cannot be processed",
    #     })
    #
    # # Build summary
    # summary_data: dict[str, Any] = summary_result.content[0] if summary_result.content else {}
    # total_data: dict[str, Any] = total_result.content[0] if total_result.content else {}
    #
    # summary: dict[str, Any] = {
    #     "total_items": len(available_items) + len(unavailable_items),
    #     "available_items": len(available_items),
    #     "unavailable_items": len(unavailable_items),
    #     "subtotal": summary_data.get("subtotal", "Rp0"),
    #     "shipping_fee": summary_data.get("shipping_fee", "Rp0"),
    #     "service_fee": summary_data.get("service_fee", "Rp0"),
    #     "total_amount": total_data.get("total_amount", "Rp0"),
    #     "savings": total_data.get("savings", ""),
    # }
    #
    # return {
    #     "items": available_items + unavailable_items,
    #     "available_items": available_items,
    #     "unavailable_items": unavailable_items,
    #     "summary": summary,
    # }
