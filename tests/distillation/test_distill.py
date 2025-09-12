import os
import urllib.parse

import pytest

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.distill import distill, load_distillation_patterns

PATTERN_LOCATIONS = {
    "http://localhost:5001/auth/email-and-password": "acme_email_and_password.html",
    "http://localhost:5001/auth/email-then-password": "acme_email_then_password.html",
}


@pytest.mark.asyncio
@pytest.mark.distill
@pytest.mark.parametrize(
    "location",
    list(PATTERN_LOCATIONS.keys()),
)
async def test_distill(location: str):
    profile = BrowserProfile()
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    assert patterns, "No patterns found to begin matching."
    async with browser_session(profile) as session:
        page = await session.page()
        hostname = urllib.parse.urlparse(location).hostname
        await page.goto(location)

        match = await distill(hostname, page, patterns)
        assert match, "No match found when one was expected."
        print(match)
        print(match.name)
        assert match.name.endswith(PATTERN_LOCATIONS[location]), "Incorrect match name found."
