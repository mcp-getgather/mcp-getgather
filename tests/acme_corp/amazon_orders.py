# ---------------------------------------------------------------------------
# Mock Amazon Orders Page
# ---------------------------------------------------------------------------

import random
from datetime import datetime, timedelta
from typing import Any

from faker import Faker
from fasthtml.common import H1, H5, A, Body, Div, Head, Html, Img, Script, Span, Title

from tests.acme_corp.acme_corp import app

# Configuration
DEFAULT_NUM_ORDERS = 50  # Default number of orders to generate
SEED = 42  # For reproducible data

# Initialize Faker with seed for reproducibility
fake = Faker()
Faker.seed(SEED)
random.seed(SEED)


# Product categories with realistic names
PRODUCT_CATEGORIES = {
    "Electronics": [
        "Wireless Mouse",
        "USB-C Cable",
        "Bluetooth Headphones",
        "Laptop Stand",
        "Webcam",
        "External Hard Drive",
        "Phone Case",
        "Screen Protector",
        "Power Bank",
        "HDMI Cable",
    ],
    "Books": [
        "Python Programming Guide",
        "Web Development Handbook",
        "Data Science Fundamentals",
        "Machine Learning Basics",
        "Cloud Computing Guide",
        "JavaScript: The Good Parts",
        "System Design Interview",
        "Clean Code",
    ],
    "Home & Kitchen": [
        "Coffee Mug",
        "Water Bottle",
        "Food Storage Container",
        "Kitchen Knife Set",
        "Non-stick Pan",
        "Cutting Board",
        "Dish Towel Set",
        "Coffee Maker",
    ],
    "Office Products": [
        "Notebook",
        "Pen Set",
        "Desk Organizer",
        "Sticky Notes",
        "Stapler",
        "Paper Clips",
        "File Folders",
        "Calculator",
    ],
    "Clothing": [
        "T-Shirt",
        "Jeans",
        "Hoodie",
        "Socks",
        "Running Shoes",
        "Winter Jacket",
        "Baseball Cap",
        "Backpack",
    ],
}


def generate_product(category: str | None = None) -> dict[str, Any]:
    """Generate a single fake product."""
    if category is None:
        category = random.choice(list(PRODUCT_CATEGORIES.keys()))

    product_name = random.choice(PRODUCT_CATEGORIES[category])
    product_id = fake.uuid4()[:8].upper()

    return {
        "name": f"{fake.company()} {product_name}",
        "url": f"/gp/product/{product_id}",
        "image_url": f"https://via.placeholder.com/100x100?text={product_name.replace(' ', '+')}",
        "product_type": category,
        "author": fake.name() if category == "Books" else fake.company(),
        "return_window": f"Return window closed on {fake.date_between(start_date='-30d', end_date='today').strftime('%b %d, %Y')}",
    }


def generate_order(order_number: int, year: int) -> dict[str, Any]:
    """Generate a single fake order."""
    # Generate random date within the year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    order_date = fake.date_time_between(start_date=start_date, end_date=end_date)

    # Generate 1-4 products per order
    num_products = random.randint(1, 4)
    products = [generate_product() for _ in range(num_products)]

    # Calculate total price
    product_prices = [random.uniform(10.0, 200.0) for _ in range(num_products)]
    total_price = sum(product_prices)

    # Generate order ID in Amazon format
    order_id = f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"

    return {
        "order_id": order_id,
        "order_date": order_date.strftime("%B %d, %Y"),
        "order_total": f"${total_price:.2f}",
        "ship_to": fake.name(),
        "products": products,
    }


def create_order_card(
    order_id: str,
    order_date: str,
    order_total: str,
    ship_to: str,
    products: list[dict[str, Any]],
):
    """Create a single order card with the structure Amazon uses."""

    # Build product items
    product_items = []
    for product in products:
        product_item = Div(
            Div(
                Div(
                    Img(src=product.get("image_url", "")),
                    cls="product-image",
                ),
                cls="item-view-left-col-inner",
            ),
            Div(
                Div(
                    A(
                        product.get("name", ""),
                        href=product.get("url", ""),
                        cls="a-link-normal",
                    ),
                    cls="yohtmlc-product-title",
                ),
                Div(
                    Span(
                        product.get("product_type", ""),
                        cls="a-size-small a-color-secondary a-text-bold",
                    ),
                    Span(product.get("author", ""), cls="a-size-small"),
                )
                if product.get("product_type") or product.get("author")
                else None,
                Span(product.get("return_window", ""), cls="a-size-small")
                if product.get("return_window")
                else None,
            ),
            cls="a-fixed-left-grid-col",
        )
        product_items.append(product_item)

    # Create order card
    return Div(
        Div(
            # Order header with date, total, ship to
            Div(
                H5(
                    Div(
                        Div("ORDER PLACED"),
                        Div(order_date),
                        cls="a-span3",
                    ),
                    Div(
                        Div("TOTAL"),
                        Div(order_total),
                        cls="a-span2",
                    ),
                    Div(
                        Div("SHIP TO"),
                        Div(
                            Div(ship_to, cls="a-popover-preload"),
                        ),
                        cls="yohtmlc-recipient",
                    ),
                ),
                # Order ID
                Div(
                    Span("ORDER # "),
                    Span(order_id),
                    cls="yohtmlc-order-id",
                ),
                cls="a-box-inner",
            ),
            # Order items
            Div(*product_items) if product_items else None,
            cls="order-card js-order-card",
        ),
        cls="a-section a-spacing-none a-padding-small",
    )


def create_orders_page(year: str, start_index: int, num_orders: int = DEFAULT_NUM_ORDERS):
    """Create the full orders page with multiple orders."""

    # Generate orders (cached by year)
    if not hasattr(create_orders_page, "_cache"):
        create_orders_page._cache = {}

    cache_key = f"{year}_{num_orders}"
    if cache_key not in create_orders_page._cache:
        # Reset seed for consistent data per year
        Faker.seed(SEED + int(year))
        random.seed(SEED + int(year))
        create_orders_page._cache[cache_key] = [
            generate_order(i, int(year)) for i in range(num_orders)
        ]

    orders = create_orders_page._cache[cache_key]

    # Filter orders by start_index for pagination
    displayed_orders = orders[start_index : start_index + 10] if start_index < len(orders) else []

    # Create order cards
    order_cards = [
        create_order_card(
            order_id=order["order_id"],
            order_date=order["order_date"],
            order_total=order["order_total"],
            ship_to=order["ship_to"],
            products=order["products"],
        )
        for order in displayed_orders
    ]

    # Build the page
    return Html(
        Head(Title(f"Your Orders - {year}")),
        Body(
            Div(
                # Navigation (simplified)
                Div(
                    Div(
                        A("Returns & Orders", href="#", id="nav-orders"),
                        id="nav-link-accountList",
                        **{"data-nav-ref": "nav_youraccount_btn"},
                    ),
                ),
                # Page header
                H1("Your Orders"),
                # Orders container - this is what the pattern looks for
                Div(
                    *order_cards,
                    cls="your-orders-content-container__content",
                ),
                cls="your-orders-content-container",
            ),
            # Navigation script (for signed-in detection)
            Script(f"""
                // Simulate Amazon navigation for signin detection
                window.addEventListener('DOMContentLoaded', function() {{
                    console.log('Orders page loaded - Year: {year}, Start Index: {start_index}, Total Orders: {len(orders)}, Displayed: {len(displayed_orders)}');
                }});
            """),
        ),
    )


@app.get("/your-orders/orders")
def amazon_orders(
    timeFilter: str = "year-2024", startIndex: int = 0, numOrders: int = DEFAULT_NUM_ORDERS
):
    """Mock Amazon orders page endpoint.

    Matches URL: https://www.amazon.com/your-orders/orders?timeFilter=year-{year}&startIndex={index}

    Query Parameters:
        timeFilter: Filter by year (e.g., "year-2024")
        startIndex: Starting index for pagination (default: 0)
        numOrders: Total number of orders to generate for the year (default: 50)
    """
    # Extract year from timeFilter (e.g., "year-2024" -> "2024")
    year = timeFilter.split("-")[-1] if "year-" in timeFilter else "2024"

    return create_orders_page(year=year, start_index=startIndex, num_orders=numOrders)
