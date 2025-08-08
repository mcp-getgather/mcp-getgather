import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastmcp import Context

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session
from getgather.parse import parse_html

amazon_mcp = BrandMCPBase(prefix="amazon", name="Amazon MCP")


@amazon_mcp.tool(tags={"private"})
async def get_purchase_history(
    ctx: Context,
) -> dict[str, Any]:
    """Get purchase/order history of a amazon."""
    return await extract(brand_id=BrandIdEnum("amazon"))


@amazon_mcp.tool
async def search_product(
    keyword: str,
    ctx: Context,
) -> dict[str, Any]:
    """Search product on amazon."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("amazon"))
    page = await browser_session.page()
    await page.goto(f"https://www.amazon.com/s?k={keyword}")
    await page.wait_for_selector("div[role='listitem']")
    await page.wait_for_timeout(1000)
    html = await page.locator("div.s-search-results").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div[role='listitem']",
        "columns": [
            {"name": "product_name", "selector": "div[data-cy='title-recipe'] > a"},
            {
                "name": "product_url",
                "selector": "div[data-cy='title-recipe'] > a",
                "attribute": "href",
            },
            {"name": "price", "selector": "div[data-cy='price-recipe']"},
            {"name": "reviews", "selector": "div[data-cy='reviews-block']"},
        ],
    })
    result = await parse_html(html_content=html, schema=spec_schema)
    return {"product_list": result.content}


@amazon_mcp.tool
async def get_product_detail(
    product_url: str,
    ctx: Context,
) -> dict[str, Any]:
    """Get product detail from amazon."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("amazon"))
    page = await browser_session.page()
    if not product_url.startswith("https"):
        product_url = f"https://www.amazon.com/{product_url}"
    await page.goto(product_url)

    await page.wait_for_selector("span#productTitle")
    await page.wait_for_timeout(1000)
    html = await page.locator("#centerCol").inner_html()
    return {"product_detail_html": html}


@amazon_mcp.tool(tags={"private"})
async def get_cart_summary(
    ctx: Context,
) -> dict[str, Any]:
    """Get cart summary from amazon."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("amazon"))
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/cart/view.html")
    await page.wait_for_selector("div#sc-active-cart")
    await page.wait_for_timeout(1000)
    html = await page.locator("div#sc-active-cart").inner_html()
    return {"cart_summary_html": html}


@amazon_mcp.tool(tags={"private"})
async def get_browsing_history(
    ctx: Context,
) -> dict[str, Any]:
    """Get browsing history from amazon."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("amazon"))
    page = await browser_session.page()
    await page.goto("https://www.amazon.com/gp/history?ref_=nav_AccountFlyout_browsinghistory")
    await page.wait_for_timeout(1000)
    await page.wait_for_selector("div[class*='desktop-grid']")
    html = await page.locator("div[class*='desktop-grid']").inner_html()
    return {"browsing_history_html": html}


@amazon_mcp.tool
async def get_calendar_event_for_return(
    return_date: str,
    product_name: str,
    order_id: str = "",
    reminder_days_before: int = 3,
    reminder_time: str | None = None,
    reminder_timezone: str | None = None,
    calendar_name: str | None = None,
    output_format: Literal["ics", "google", "both"] = "ics",
) -> dict[str, Any]:
    """Generate an ICS calendar event for Amazon product return deadline.

    Parameters
    - return_date: The return deadline date. Supported formats: 'Month DD, YYYY' or 'YYYY-MM-DD'.
    - product_name: The product name to include in summary/description.
    - order_id: Optional order identifier.
    - reminder_days_before: Days before the return date to trigger the reminder (default 3).
    - reminder_time: Optional local time for the reminder in HH:MM (24h). If provided with timezone,
      an absolute alarm is used at that local time on (return_date - days).
    - reminder_timezone: Optional IANA timezone (e.g., 'America/Los_Angeles'). Used with reminder_time.
    - calendar_name: Optional calendar name hint added as X-WR-CALNAME in VCALENDAR.
    - output_format: Output format - 'ics' (default), 'google' (pre-filled link), or 'both'.
    """

    def escape_ics_text(value: str) -> str:
        """Escape text per RFC 5545 for TEXT values."""
        return (
            value.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")
        )

    try:
        return_dt = datetime.strptime(return_date, "%B %d, %Y")
    except ValueError:
        try:
            return_dt = datetime.strptime(return_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use 'Month DD, YYYY' or 'YYYY-MM-DD'"}

    reminder_dt = return_dt - timedelta(days=reminder_days_before)

    event_uid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return_date_str = return_dt.strftime("%Y%m%d")

    title_raw = (
        f"Amazon Return Deadline: {product_name[:50]}{'...' if len(product_name) > 50 else ''}"
    )
    description_raw = f"Return deadline for Amazon order"
    if order_id:
        description_raw += f" #{order_id}"
    description_raw += (
        f"\nProduct: {product_name}\nReturn by: {return_date}\nGenerated by GetGather MCP"
    )

    title = escape_ics_text(title_raw)
    description = escape_ics_text(description_raw)

    # Build alarm trigger.
    trigger_line: str = f"TRIGGER:-P{max(0, int(reminder_days_before))}D"
    alarm_desc = escape_ics_text(f"Return deadline in {reminder_days_before} days: {product_name}")

    if reminder_time and reminder_timezone:
        try:
            # Parse HH:MM
            time_dt = datetime.strptime(reminder_time, "%H:%M")
            zone = ZoneInfo(reminder_timezone)
            reminder_local = datetime(
                year=return_dt.year,
                month=return_dt.month,
                day=return_dt.day,
                hour=time_dt.hour,
                minute=time_dt.minute,
                tzinfo=zone,
            ) - timedelta(days=reminder_days_before)
            reminder_utc = reminder_local.astimezone(timezone.utc)
            trigger_line = f"TRIGGER;VALUE=DATE-TIME:{reminder_utc.strftime('%Y%m%dT%H%M%SZ')}"
        except Exception:
            # If parsing fails, keep the relative trigger
            pass

    # If absolute_trigger_built is False, trigger_line remains as the relative trigger above

    # Optional VCALENDAR headers (some clients honor these on import)
    vcal_extra_lines: list[str] = []
    if calendar_name:
        vcal_extra_lines.append(f"X-WR-CALNAME:{escape_ics_text(calendar_name)}")
    if reminder_timezone:
        vcal_extra_lines.append(f"X-WR-TIMEZONE:{escape_ics_text(reminder_timezone)}")
    vcal_header = ("\n".join(vcal_extra_lines) + "\n") if vcal_extra_lines else ""

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//GetGather//Amazon Return Reminder//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
{vcal_header}BEGIN:VEVENT
UID:{event_uid}
DTSTART;VALUE=DATE:{return_date_str}
DTEND;VALUE=DATE:{return_date_str}
DTSTAMP:{now}
SUMMARY:{title}
DESCRIPTION:{description}
CATEGORIES:Amazon,Returns,Shopping
PRIORITY:5
STATUS:CONFIRMED
TRANSP:TRANSPARENT
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:{alarm_desc}
{trigger_line}
END:VALARM
END:VEVENT
END:VCALENDAR"""

    # Generate Google Calendar pre-filled link
    google_link = None
    if output_format in ("google", "both"):
        # Format dates for Google Calendar (YYYYMMDD format)
        start_date = return_dt.strftime("%Y%m%d")
        end_date = return_dt.strftime("%Y%m%d")

        # Google Calendar URL parameters
        google_params = {
            "action": "TEMPLATE",
            "text": title_raw,
            "dates": f"{start_date}/{end_date}",
            "details": description_raw.replace("\n", "\\n"),
            "ctz": reminder_timezone or "UTC",
        }

        google_link = f"https://calendar.google.com/calendar/render?{urlencode(google_params)}"

    # Build return response based on output format
    result: dict[str, Any] = {
        "event_details": {
            "title": title_raw,
            "return_date": return_date,
            "product_name": product_name,
            "order_id": order_id,
            "reminder_date": reminder_dt.strftime("%B %d, %Y"),
            "calendar_name": calendar_name or "",
        },
    }

    if output_format in ("ics", "both"):
        result["ics_content"] = ics_content
        result["filename"] = f"amazon_return_{order_id or event_uid[:8]}.ics"

    if output_format in ("google", "both"):
        result["google_calendar_link"] = google_link

    return result
