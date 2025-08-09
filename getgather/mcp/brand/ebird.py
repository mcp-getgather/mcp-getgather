from typing import Any

from getgather.connectors.spec_loader import BrandIdEnum
from getgather.connectors.spec_models import Schema as SpecSchema
from getgather.mcp.registry import BrandMCPBase
from getgather.mcp.shared import extract, start_browser_session
from getgather.parse import parse_html

ebird_mcp = BrandMCPBase(prefix="ebird", name="Ebird MCP")


@ebird_mcp.tool(tags={"private"})
async def get_life_list() -> dict[str, Any]:
    """Get life list of a ebird."""
    return await extract(brand_id=BrandIdEnum("ebird"))


@ebird_mcp.tool
async def get_explore_species_list(
    keyword: str,
) -> dict[str, Any]:
    """Get species list from ebird to be explored."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("ebird"))
    page = await browser_session.page()
    await page.goto(f"https://ebird.org/explore")
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
    result = await parse_html(html_content=html, schema=spec_schema)
    return {"species_list": result.content}


@ebird_mcp.tool
async def explore_species(
    sci_name: str,
) -> dict[str, Any]:
    """Explore species on Ebird from get_explore_species_list."""
    browser_session = await start_browser_session(brand_id=BrandIdEnum("ebird"))
    page = await browser_session.page()
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
