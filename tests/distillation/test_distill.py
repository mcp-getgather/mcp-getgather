from getgather.distill import distill, load_distillation_patterns
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
import os
import pytest


@pytest.mark.asyncio
async def test_distill():
    profile = BrowserProfile()
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    print(patterns)
    assert patterns
    async with browser_session(profile) as session:
        page = await session.page()
        match = await distill("http://localhost:5001/auth/email-and-password", page, patterns)
        assert match
