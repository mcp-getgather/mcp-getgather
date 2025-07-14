import pytest
from playwright.sync_api import Page, expect

expect.set_options(timeout=2_000)


@pytest.fixture(scope="session")
def site_url() -> str:
    return "http://localhost:8000"


@pytest.fixture(autouse=True)
def configure_playwright_timeouts(page: Page):
    page.set_default_timeout(10_000)
    page.set_default_navigation_timeout(10_000)

    yield page
