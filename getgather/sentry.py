from datetime import datetime
from pathlib import Path
from typing import Any

import sentry_sdk

from getgather.config import settings


def setup_error_context(
    scope: sentry_sdk.Scope,
    e: Exception,
    brand_id: str,
    error_type: str,
    flow_state: dict[str, Any],
    browser_profile_id: str,
    page_content: str | None = None,
    screenshot_path: Path | None = None,
) -> None:
    """Set up Sentry scope context for error reporting.

    Args:
        scope: The Sentry scope to configure
        e: The exception to capture
        brand_id: The brand ID associated with the error
        error_type: The type of error (e.g. 'auth_flow_error',
            'extract_flow_error')
        flow_state: The flow state at the time of error
        browser_profile_id: The browser profile ID
        page_content: Optional HTML content of the page
        screenshot_path: Optional path to the screenshot
    """
    filename = f"{browser_profile_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
    filepath = settings.screenshots_dir / filename

    scope.set_tag("brand_id", brand_id)
    scope.set_tag("error_type", error_type)
    scope.set_context("flow_state", flow_state)
    scope.fingerprint = ["{{ default }}", str(e)]

    if screenshot_path:
        scope.add_attachment(
            filename=filename,
            path=str(screenshot_path),
        )

    if page_content:
        html_path = filepath.with_suffix(".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page_content)
        scope.add_attachment(
            filename=filename.replace(".png", ".html"),
            path=str(html_path),
        )


def attach_to_sentry(filepath: Path, scope: sentry_sdk.Scope | None = None):
    if not scope:
        with sentry_sdk.isolation_scope() as scope:
            scope.add_attachment(filename=filepath.name, path=str(filepath))
            sentry_sdk.capture_message(f"Attached {filepath.name} to Sentry")
    else:
        scope.add_attachment(filename=filepath.name, path=str(filepath))


# ---------------------------------------------------------------------------
# User context helpers
# ---------------------------------------------------------------------------
_USER_KEYS = ("email", "username", "user", "login")


def _extract_user_identifier(inputs: dict[str, str] | None) -> str | None:
    """Return the first email/username value found in *inputs*.

    Inputs come from ``FlowState.inputs`` which stores values users provide
    while completing the auth flow.
    """

    if not inputs:
        return None

    for key in _USER_KEYS:
        if value := inputs.get(key):
            return value.strip()
    return None


def set_user_context(
    inputs: dict[str, str] | None,
    scope: sentry_sdk.Scope | None = None,
) -> bool:
    """Attach user information to Sentry based on ``inputs``.

    When *scope* is given, the user is set on that scope; otherwise the
    globally active scope is used. The function returns ``True`` if a user was
    found and attached, ``False`` otherwise.
    """

    identifier = _extract_user_identifier(inputs)
    if not identifier:
        return False

    user_info: dict[str, str]
    if "@" in identifier:
        user_info = {"email": identifier}
    else:
        user_info = {"username": identifier}

    if scope is None:
        sentry_sdk.set_user(user_info)
    else:
        scope.set_user(user_info)

    return True
