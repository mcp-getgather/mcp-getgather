from datetime import datetime
from typing import Any

from patchright.async_api import Page

from getgather.brand_state import brand_state_manager
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, get_mcp_browser_session, with_brand_browser_session
from getgather.parse import parse_html

ebird_mcp = BrandMCPBase(brand_id="ebird", name="Ebird MCP")


@ebird_mcp.tool(tags={"private"})
async def get_life_list() -> dict[str, Any]:
    """Get life list of a ebird."""
    return await extract()


@ebird_mcp.tool
async def get_explore_species_list(
    keyword: str,
) -> dict[str, Any]:
    """Get species list from ebird to be explored."""
    if await brand_state_manager.is_brand_connected(ebird_mcp.brand_id):
        profile_id = await brand_state_manager.get_browser_profile_id(ebird_mcp.brand_id)
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        await page.goto("https://ebird.org/explore")
        await page.wait_for_timeout(1000)
        await page.type("input#species", keyword)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1000)
        await page.wait_for_selector("div#Suggest-dropdown-species")
        html = await page.locator("div#Suggest-dropdown-species").inner_html()
    spec_schema = SpecSchema.model_validate({
        "bundle": "",
        "format": "html",
        "output": "",
        "row_selector": "div[role='option']",
        "columns": [
            {"name": "species_name", "selector": "span.Suggestion-text"},
            {"name": "sci_name", "selector": "span.Suggestion-text span"},
        ],
    })
    result = await parse_html(brand_id=ebird_mcp.brand_id, html_content=html, schema=spec_schema)
    return {"species_list": result.content}


@ebird_mcp.tool
async def explore_species(
    sci_name: str,
) -> dict[str, Any]:
    """Explore species on Ebird from get_explore_species_list."""
    if await brand_state_manager.is_brand_connected(ebird_mcp.brand_id):
        profile_id = await brand_state_manager.get_browser_profile_id(ebird_mcp.brand_id)
        profile = BrowserProfile(id=profile_id) if profile_id else BrowserProfile()
    else:
        profile = BrowserProfile()

    async with browser_session(profile) as session:
        page = await session.page()
        # Navigate to explore and search for the species by scientific name
        await page.goto("https://ebird.org/explore")
        await page.wait_for_selector("input#species")
        await page.fill("input#species", sci_name)
        await page.keyboard.press("Enter")
        await page.wait_for_selector("div#Suggest-dropdown-species")
        await (
            page.locator("div#Suggest-dropdown-species")
            .locator("span.Suggestion-text span")
            .get_by_text(sci_name)
            .click()
        )
        await page.wait_for_load_state("domcontentloaded")
        species_description_html = await page.locator("div.Hero-content").inner_html()
        species_identification_html = await page.locator("div.Species-identification").inner_html()
        species_statistic_html = await page.locator("div.Species-regionalData-stats").inner_html()
    return {
        "species_description_html": species_description_html,
        "species_identification_html": species_identification_html,
        "species_statistic_html": species_statistic_html,
    }


@ebird_mcp.tool(tags={"private"})
@with_brand_browser_session
async def submit_checklist(
    location: str,
    birds: list[str],
    checklist_datetime: datetime,
    duration_hours: str = "1",
    distance: str = "1",
):
    """Submit checklist to ebird."""
    session = get_mcp_browser_session()
    page = await session.page()
    await page.goto("https://ebird.org/submit")
    await page.wait_for_selector("select#myLocSel")
    await page.wait_for_timeout(1000)

    await select_location(page, location)
    await page.click("input[type=submit]")
    await select_date(page, checklist_datetime)
    await select_trip_details(page, checklist_datetime, duration_hours, distance)

    await page.click("button[type=submit]")
    await page.wait_for_selector("input[name=jumpToSpp]")

    await add_birds_to_checklist(page, birds)

    await page.click("input#all-spp-n")
    await page.click("button[type=submit]")


async def select_location(page: Page, location: str):
    """Select location for checklist."""
    await page.select_option("#myLocSel", location)
    await page.wait_for_timeout(1000)


async def select_date(page: Page, checklist_datetime: datetime):
    """Select date for checklist."""
    current_month = datetime.now().month
    checklist_month = checklist_datetime.month
    day = str(checklist_datetime.day)

    await page.wait_for_selector("select#p-month")

    # Only select month if it's different from current month
    if checklist_month != current_month:
        await page.select_option("#p-month", str(checklist_month))
    await page.wait_for_timeout(1000)
    await page.select_option("#p-day", day)
    await page.wait_for_timeout(1000)


async def select_trip_details(
    page: Page, checklist_datetime: datetime, duration_hours: str, distance: str
):
    """Select trip details including time, duration, and distance."""
    # Extract hour, minute, and AM/PM from datetime object
    hour = str(checklist_datetime.hour % 12 or 12)  # Convert to 12-hour format
    minute = str(checklist_datetime.minute).zfill(2)
    am_pm = "AM" if checklist_datetime.hour < 12 else "PM"

    await page.click("label:has-text('Traveling')")
    await page.fill("input#p-shared-hr", hour)
    await page.fill("input#p-shared-min", minute)
    await page.select_option("#p-shared-ampm", am_pm)
    await page.fill("input#p-dur-hrs", duration_hours)
    await page.fill("input#p-dist", distance)
    await page.fill("input#p-party-size", "1")


async def add_birds_to_checklist(page: Page, birds: list[str]):
    """Add birds to checklist with case-insensitive partial matching."""
    try:
        for bird in birds:
            bird_locator = page.locator("li").filter(has_text=bird)
            if await bird_locator.count() == 0:
                continue

            inner_element = bird_locator.first
            input_field = inner_element.locator("input.sc")
            await input_field.fill(str(1))
    except Exception as e:
        raise e
