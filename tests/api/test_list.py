import pytest
from playwright.sync_api import Page, expect

from getgather.connectors.spec_loader import brand_id_list


@pytest.mark.webui
def test_list(page: Page, site_url: str):
    page.goto(site_url)

    brands_grid = page.get_by_test_id("brands-grid")
    expect(brands_grid).to_have_count(1)

    brand_cards = brands_grid.locator("a[data-testid^=brand-card_]")
    expect(brand_cards).to_have_count(len(brand_id_list()))

    for card in brand_cards.all():
        testid = card.get_attribute("data-testid")
        assert testid is not None
        brand_id = testid.split("_")[-1]
        expect(card).to_have_attribute("href", f"/start/{brand_id}")

    expect(page).to_have_title("GetGather")
