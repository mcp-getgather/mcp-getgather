import json
from typing import Any
from urllib.parse import quote, urlparse

from getgather.actions import handle_graphql_response
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import start_browser_session
from getgather.parse import parse_html

tokopedia_mcp = BrandMCPBase(prefix="tokopedia", name="Tokopedia MCP")


@tokopedia_mcp.tool
async def search_product(
    keyword: str,
) -> dict[str, Any]:
    """Search product on tokopedia."""
    if BrandState.is_brand_connected(BrandIdEnum("tokopedia")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("tokopedia"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        # URL encode the search keyword
        encoded_keyword = quote(keyword)
        await page.goto(
            f"https://www.tokopedia.com/search?q={encoded_keyword}", wait_until="commit"
        )
        await page.wait_for_selector(
            "div[data-testid='divSRPContentProducts'] > div:nth-child(1) > div:nth-child(1)"
        )
        await page.wait_for_timeout(2000)
        html = await page.locator("div[data-testid='divSRPContentProducts']").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div[class='css-5wh65g']",
        "columns": [
            {"name": "product_name", "selector": "a > div > div:nth-child(2) > div:nth-child(1)"},
            {"name": "product_url", "selector": "a", "attribute": "href"},
            {"name": "price_discount", "selector": "div[class='rJTRB7icxB2aB4uO48TY0Q==']"},
            {"name": "price", "selector": "div[class*='urMOIDHH7I0Iy1Dv2oFaNw==']"},
            {"name": "product_summary", "selector": "div[class='c7W9YYbRQuC29+GfsfRTEA==']"},
        ],
    })
    result = await parse_html(
        brand_id=BrandIdEnum("tokopedia"), html_content=html, schema=spec_schema
    )
    return {"product_list": result.content}


@tokopedia_mcp.tool
async def get_product_details(
    product_url: str,
) -> dict[str, Any]:
    """Get product details from tokopedia. Get product_url from search_product tool."""
    if BrandState.is_brand_connected(BrandIdEnum("tokopedia")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("tokopedia"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto(product_url, wait_until="commit")
        await page.wait_for_selector("h1[data-testid='lblPDPDetailProductName']")
        await page.wait_for_timeout(2000)
        html = await page.locator("body").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div#main-pdp-container",
        "columns": [
            {"name": "product_name", "selector": "h1[data-testid='lblPDPDetailProductName']"},
            {
                "name": "product_sold_count",
                "selector": "p[data-testid='lblPDPDetailProductSoldCounter']",
            },
            {
                "name": "rating_number",
                "selector": "span[data-testid='lblPDPDetailProductRatingNumber']",
            },
            {
                "name": "rating_count",
                "selector": "div[data-testid='lblPDPDetailProductRatingCounter']",
            },
            {"name": "price", "selector": "div[data-testid='lblPDPDetailProductPrice']"},
            {
                "name": "discount_percentage",
                "selector": "span[data-testid='lblPDPDetailDiscountPercentage']",
            },
            {"name": "original_price", "selector": "span[data-testid='lblPDPDetailOriginalPrice']"},
            {"name": "variant", "selector": "div#pdpVariantContainer"},
            {"name": "description", "selector": "div[data-testid='lblPDPDescriptionProduk']"},
            {"name": "shop_name", "selector": "div[data-testid='llbPDPFooterShopName']"},
        ],
    })
    result = await parse_html(
        brand_id=BrandIdEnum("tokopedia"), html_content=html, schema=spec_schema
    )
    return {"product_detail": result.content}


@tokopedia_mcp.tool
async def search_shop(
    keyword: str,
) -> dict[str, Any]:
    """Search shop on tokopedia."""
    if BrandState.is_brand_connected(BrandIdEnum("tokopedia")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("tokopedia"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        # URL encode the search keyword
        encoded_keyword = quote(keyword)
        await page.goto(
            f"https://www.tokopedia.com/search?st=shop&q={encoded_keyword}", wait_until="commit"
        )
        await page.wait_for_selector(
            "div[data-testid='divShopContainer'] > div:nth-child(1) > div:nth-child(1)"
        )
        await page.wait_for_timeout(2000)
        html = await page.locator("div[data-testid='divShopContainer']").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div[data-testid='shop-card']",
        "columns": [
            {"name": "shop_name", "selector": "span[data-testid='spnSRPShopName']"},
            {"name": "shop_location", "selector": "div[data-testid='dSRPShopLocation']"},
            {
                "name": "shop_url",
                "selector": "a[data-testid='shop-card-header']",
                "attribute": "href",
            },
            {
                "name": "shop_highlight_product_urls",
                "multiple": True,
                "selector": "a[data-testid='shop-card-product']",
                "attribute": "href",
            },
            {
                "name": "shop_highlight_product_imgs",
                "multiple": True,
                "selector": "a[data-testid='shop-card-product'] img",
                "attribute": "src",
            },
            {
                "name": "shop_highlight_product_prices",
                "multiple": True,
                "selector": "a[data-testid='shop-card-product'] span",
            },
        ],
    })
    result = await parse_html(
        brand_id=BrandIdEnum("tokopedia"), html_content=html, schema=spec_schema
    )
    return {"shop_list": result.content}


@tokopedia_mcp.tool
async def get_shop_details(
    product_url: str | None = None,
    shop_url: str | None = None,
) -> dict[str, Any]:
    """Get store details from tokopedia by product_url or shop_url. Get product_url from search_product tool or shop_url from search_shop tool.
    If both are provided, shop_url takes precedence."""
    if not product_url and not shop_url:
        return {"error": "Either product_url or shop_url must be provided"}

    # If shop_url is provided, use it directly after validation
    target_url = None
    if shop_url:
        try:
            parsed_shop = urlparse(shop_url)
            if not all([parsed_shop.scheme, parsed_shop.netloc]):
                return {"error": "Invalid shop URL - missing scheme or domain"}
            if not parsed_shop.netloc.endswith("tokopedia.com"):
                return {"error": "Invalid shop URL - must be a tokopedia.com domain"}
            target_url = shop_url
        except Exception:
            return {"error": "Invalid shop URL format"}

    # Only try to derive from product_url if we don't have a valid shop_url
    if not target_url and product_url:
        try:
            parsed = urlparse(product_url)
            if not all([parsed.scheme, parsed.netloc]):
                return {"error": "Invalid product URL - missing scheme or domain"}
            if not parsed.netloc.endswith("tokopedia.com"):
                return {"error": "Invalid product URL - must be a tokopedia.com domain"}

            # Split path and filter out empty segments
            path_parts = [part for part in parsed.path.split("/") if part]
            if not path_parts:
                return {
                    "error": "Invalid product URL - cannot derive shop URL from root or empty path"
                }

            shop_segment = path_parts[0]
            if not shop_segment:
                return {"error": "Invalid product URL - cannot derive shop name from URL"}

            target_url = f"{parsed.scheme}://{parsed.netloc}/{shop_segment}"
        except Exception:
            return {"error": "Invalid product URL format"}

    if not target_url:
        return {"error": "Could not determine valid shop URL"}

    if BrandState.is_brand_connected(BrandIdEnum("tokopedia")):
        profile_id = BrandState.get_browser_profile_id(BrandIdEnum("tokopedia"))
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto(target_url, wait_until="commit")
        await page.wait_for_selector("h1[data-testid='shopNameHeader']")
        await page.wait_for_timeout(2000)
        html = await page.locator("div#zeus-root").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div[data-ssr='shopSSR']",
        "columns": [
            {"name": "shop_name", "selector": "h1[data-testid='shopNameHeader']"},
            {"name": "shop_location", "selector": "span[data-testid='shopLocationHeader']"},
            {"name": "shop_rating", "selector": "div[data-testid='shopRatingDetailHeader']"},
        ],
    })
    result = await parse_html(
        brand_id=BrandIdEnum("tokopedia"), html_content=html, schema=spec_schema
    )
    return {"shop_detail": result.content}


@tokopedia_mcp.tool(tags={"private"})
async def get_purchase_history(
    page_number: int = 1,
) -> dict[str, Any]:
    """Get purchase history of a tokopedia."""

    browser_session = await start_browser_session(brand_id=BrandIdEnum("tokopedia"))
    page = await browser_session.page()
    await page.goto(f"https://www.tokopedia.com/order-list?page={page_number}")
    raw_data = await handle_graphql_response(
        page,
        "https://gql.tokopedia.com/graphql/GetOrderHistory",
        "GetOrderHistory",
    )
    results: list[dict[str, Any]] = []
    if raw_data:
        uoh_orders = raw_data[0].get("data", {}).get("uohOrders", {})
        orders = uoh_orders.get("orders", [])
        for order in orders:
            metadata = order.get("metadata", {})
            shop = json.loads(metadata.get("queryParams", "{}"))
            list_product_str = order.get("metadata", {}).get("listProducts", "[]")

            product_results: list[dict[str, Any]] = order.get("metadata", {}).get("products", [])
            if list_product_str != "":
                product_results = []
                products = json.loads(list_product_str)
                for product in products:
                    product_result = {
                        "product_name": product.get("product_name", ""),
                        "product_price": product.get("product_price", ""),
                        "original_price": product.get("original_price", ""),
                        "quantity": product.get("quantity", ""),
                    }
                    product_results.append(product_result)
            result = {
                "shop_name": shop.get("shop_name", ""),
                "products": product_results,
                "purchase_detail_url": f"https://www.tokopedia.com{metadata.get('detailURL', {}).get('webURL')}",
                "payment_date": metadata.get("paymentDate", ""),
                "status": metadata.get("status", {}).get("label", ""),
                "total_price": metadata.get("totalPrice", {}).get("value", ""),
            }
            results.append(result)

    return {"purchase_history": results, "page": page_number}


@tokopedia_mcp.tool(tags={"private"})
async def get_cart() -> dict[str, Any]:
    """Get cart of a tokopedia."""

    browser_session = await start_browser_session(brand_id=BrandIdEnum("tokopedia"))
    page = await browser_session.page()
    await page.goto(f"https://www.tokopedia.com/cart")
    raw_data = await handle_graphql_response(
        page,
        "https://gql.tokopedia.com/graphql/cart_revamp_v4",
        "cart_revamp_v4",
    )
    results: list[dict[str, Any]] = []
    if raw_data:
        carts = (
            raw_data[0]
            .get("data", {})
            .get("cart_revamp_v4", {})
            .get("data", {})
            .get("available_section", {})
            .get("available_group", [])
        )
        for cart in carts:
            products: list[dict[str, Any]] = []
            for shop_cart in cart.get("group_shop_v2_cart", []):
                for shop_cart_detail in shop_cart.get("cart_details", []):
                    for product in shop_cart_detail.get("products", []):
                        products.append({
                            "product_name": product.get("product_name", ""),
                            "product_price": product.get("product_price", ""),
                            "product_url": product.get("product_url", ""),
                            "product_quantity": product.get("product_quantity", ""),
                        })
            result = {
                "shop_name": cart.get("group_information", {}).get("name", ""),
                "products": products,
            }
            results.append(result)

    return {"cart": results}


@tokopedia_mcp.tool(tags={"private"})
async def get_wishlist(
    page_number: int = 1,
) -> dict[str, Any]:
    """Get purchase history of a tokopedia."""

    browser_session = await start_browser_session(brand_id=BrandIdEnum("tokopedia"))
    page = await browser_session.page()
    await page.goto(f"https://www.tokopedia.com/wishlist/all?page={page_number}")
    raw_data = await handle_graphql_response(
        page,
        "https://gql.tokopedia.com/graphql/GetWishlistCollectionItems",
        "GetWishlistCollectionItems",
    )
    results: list[dict[str, Any]] = []
    if raw_data:
        uoh_orders = raw_data[0].get("data", {}).get("get_wishlist_collection_items", {})
        wishlists = uoh_orders.get("items", [])
        for wishlist in wishlists:
            result = {
                "product_name": wishlist.get("name", ""),
                "available": wishlist.get("available", ""),
                "label_stock": wishlist.get("label_stock", ""),
                "min_order": wishlist.get("min_order", ""),
                "original_price": wishlist.get("original_price", ""),
                "price": wishlist.get("price", ""),
                "sold_count": wishlist.get("sold_count", ""),
                "shop_name": wishlist.get("shop", {}).get("name", ""),
            }
            results.append(result)

    return {"wishlist": results}
