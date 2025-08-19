from typing import Any

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, get_mcp_browser_session, with_brand_browser_session
from getgather.parse import parse_html
from patchright.async_api import Page

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
    if BrandState.is_brand_connected(ebird_mcp.brand_id):
        profile_id = BrandState.get_browser_profile_id(ebird_mcp.brand_id)
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
    if BrandState.is_brand_connected(ebird_mcp.brand_id):
        profile_id = BrandState.get_browser_profile_id(ebird_mcp.brand_id)
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
    month: str,
    day: str,
    start_time: str,
    am_pm: str,
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
    await select_date(page, month, day)
    await select_trip_details(page, start_time, duration_hours, distance, am_pm)

    print(f"🧭 Going to checklist")
    await page.click("button[type=submit]")
    await page.wait_for_selector("input[name=jumpToSpp]")

    print(f"🦆 Adding birds")
    await add_birds_to_checklist(page, birds)

    print(f"✅ Submitting checklist")
    await page.click("input#all-spp-n")
    await page.click("button[type=submit]")


async def select_location(page: Page, location: str):
    """Select location for checklist."""
    print(f"🌎 Selecting location: {location}")
    await page.select_option("#myLocSel", location)
    await page.wait_for_timeout(1000)


async def select_date(page: Page, month: str, day: str):
    """Select date for checklist."""
    print(f"📆 Selecting date: {month}/{day}")
    await page.wait_for_selector("select#p-month")
    await page.select_option("#p-month", month)
    await page.select_option("#p-day", day)


async def select_trip_details(page: Page, start_time: str, duration_hours: str, distance: str, am_pm: str):
    """Select trip details including time, duration, and distance."""
    # Parse hour and minute from start_time (format: "5:23")
    time_parts = start_time.split(":")
    hour = time_parts[0]
    minute = time_parts[1] if len(time_parts) > 1 else "00"
    
    print(f"🚶🏻 Selecting trip details: {hour}:{minute}, {duration_hours}h, {distance}mi")
    await page.click("label:has-text('Traveling')")
    await page.fill("input#p-shared-hr", hour)
    await page.fill("input#p-shared-min", minute)
    await page.select_option("#p-shared-ampm", am_pm.upper())
    await page.fill("input#p-dur-hrs", duration_hours)
    await page.fill("input#p-dist", distance)
    await page.fill("input#p-party-size", "1")


async def add_birds_to_checklist(page: Page, birds: list[str]):
    """Add birds to checklist with case-insensitive partial matching."""
    for bird in birds:
        inner_element = page.locator("li").filter(has_text=bird).first
        if await inner_element.count() == 0:
            print(f"⚠️  Could not find bird: {bird}")
            continue

        input_field = inner_element.locator("input.sc")
        await input_field.fill(str(1))
