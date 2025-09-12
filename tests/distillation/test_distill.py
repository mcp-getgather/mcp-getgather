import os
import urllib.parse

import pytest

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.distill import distill, load_distillation_patterns


@pytest.mark.asyncio
async def test_distill():
    profile = BrowserProfile()
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    assert patterns, "No patterns found to begin matching."
    location = "http://localhost:5001/auth/email-and-password"  # hardcoded for now, will be parameterized later
    async with browser_session(profile) as session:
        page = await session.page()
        hostname = urllib.parse.urlparse(location).hostname
        await page.goto(location)

        match = await distill(hostname, page, patterns)
        assert match, "No match found when one was expected."
        assert match.name.endswith("acme_email_and_password.html"), "Incorrect match name found."
