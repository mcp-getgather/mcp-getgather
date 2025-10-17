import os
import urllib.parse

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.distill import distill, load_distillation_patterns, run_distillation_loop

DISTILL_PATTERN_LOCATIONS = {
    "http://localhost:5001": "acme_home_page.html",
    "http://localhost:5001/auth/email-and-password": "acme_email_and_password.html",
    "http://localhost:5001/auth/email-then-password": "acme_email_only.html",
    "http://localhost:5001/auth/email-and-password-checkbox": "acme_email_and_password_checkbox.html",
    "http://localhost:5001/universal-error-test": "acme_universal_error_test.html",
}

SIGN_IN_PATTERN_ENDPOINTS = [
    "http://localhost:5001/auth/email-and-password",
    "http://localhost:5001/auth/email-and-password-checkbox",
    "http://localhost:5001/auth/email-then-password",
    "http://localhost:5001/auth/email-then-otp",
    "http://localhost:5001/auth/email-and-password-then-mfa",
]


@pytest.mark.asyncio
@pytest.mark.distill
@pytest.mark.parametrize(
    "location",
    list(DISTILL_PATTERN_LOCATIONS.keys()),
)
async def test_distill(location: str):
    """Tests the distill function's most basic ability to match a simple pattern."""
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
        assert match.name.endswith(DISTILL_PATTERN_LOCATIONS[location]), (
            "Incorrect match name found."
        )


@pytest.mark.asyncio
@pytest.mark.distill
@pytest.mark.parametrize(
    "location",
    SIGN_IN_PATTERN_ENDPOINTS,
)
async def test_distillation_loop(location: str):
    """Tests the distillation loop with email and password autofill."""
    profile = BrowserProfile()
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    assert patterns, "No patterns found to begin matching."

    result, _ = await run_distillation_loop(
        location=location,
        patterns=patterns,
        browser_profile=profile,
        timeout=30,
        interactive=True,
    )
    assert result, "No result found when one was expected."
