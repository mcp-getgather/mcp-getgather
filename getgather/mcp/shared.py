from typing import Any

from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum

from getgather.flow_state import FlowState

from getgather.mcp.session_manager import SessionManager

from getgather.extract_orchestrator import ExtractOrchestrator


from getgather.browser.session import BrowserSession

from patchright.async_api import Page

from getgather.auth_flow import auth_flow, AuthFlowRequest, ExtractResult

from fastmcp.server.dependencies import get_http_headers
from getgather.config import settings


from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)


def get_brand_inputs(brand_id: BrandIdEnum) -> dict[str, str]:
    headers = get_http_headers()

    uppercase_headers = {k.upper(): v for k, v in headers.items()}

    brand_inputs: dict[str, dict[str, str]] = {
        "goodreads": {
            "email": uppercase_headers.get("GOODREADS_EMAIL", settings.GOODREADS_EMAIL),
            "password": uppercase_headers.get("GOODREADS_PASSWORD", settings.GOODREADS_PASSWORD),
        },
        "bbc": {
            "email": uppercase_headers.get("BBC_EMAIL", settings.BBC_EMAIL),
            "password": uppercase_headers.get("bbc_password", settings.BBC_PASSWORD),
            "continue": "true",
            "submit": "true",
        },
        "zillow": {
            "email": uppercase_headers.get("ZILLOW_EMAIL", settings.ZILLOW_EMAIL),
            "password": uppercase_headers.get("zillow_password", settings.ZILLOW_PASSWORD),
            "continue": "true",
            "submit": "true",
        },
        "ebird": {
            "username": uppercase_headers.get("EBIRD_USERNAME", settings.EBIRD_USERNAME),
            "password": uppercase_headers.get("ebird_password", settings.EBIRD_PASSWORD),
            "submit": "true",
        },
    }

    inputs = brand_inputs[brand_id]

    # Validate all inputs are present and not empty
    missing_keys = [k for k, v in inputs.items() if not v]
    if missing_keys:
        raise ValueError(
            f"Missing or empty input(s) for: {', '.join(missing_keys)}. Please provide the missing inputs in the headers or environment variables."
        )

    return inputs


async def auth(
    brand_id: BrandIdEnum,
    session_id: str | None = None,
) -> dict[str, Any]:
    profile_id = SessionManager.get_browser_profile_id(session_id=session_id)

    auth_request = AuthFlowRequest(
        profile_id=profile_id,
        state=FlowState(inputs=get_brand_inputs(brand_id)),
        extract=False,
    )
    auth_response = await auth_flow(brand_id, auth_request)
    if auth_response.state.finished:
        SessionManager.update_connected_brand(brand_id=brand_id, session_id=session_id)
        return {
            "status": auth_response.status,
        }
    else:
        return {
            "current_page_spec_name": auth_response.state.current_page_spec_name,
            "prompt": auth_response.state.prompt,
            "status": auth_response.status,
            "error": auth_response.state.error,
        }


async def extract(
    brand_id: BrandIdEnum,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Extract data from a brand."""

    profile_id = SessionManager.get_browser_profile_id(session_id=session_id)
    browser_profile = BrowserProfile.get(profile_id=profile_id)

    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()

    extract_orchestrator = ExtractOrchestrator(
        brand_id=brand_id,
        browser_profile=browser_profile,
        nested_browser_session=True,
    )
    await extract_orchestrator.extract_flow()
    await browser_session.stop()
    extract_result = ExtractResult(
        profile_id=browser_profile.profile_id,
        state=extract_orchestrator.state,
        bundles=extract_orchestrator.bundles,
    )

    parsed_bundles = [bundle for bundle in extract_result.bundles if bundle.parsed]
    return {
        "extract_result": parsed_bundles if parsed_bundles else extract_result.bundles,
    }


async def start_browser_session(
    session_id: str | None = None,
) -> Page:
    profile_id = SessionManager.get_browser_profile_id(session_id=session_id)
    browser_profile = BrowserProfile.get(profile_id=profile_id)

    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()
    return await browser_session.page()
