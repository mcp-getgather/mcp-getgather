
from typing import Any

from getgather.browser.profile import BrowserProfile
from getgather.connectors.spec_loader import BrandIdEnum

from getgather.flow_state import FlowState

from getgather.mcp.session_manager import SessionManager

from getgather.extract_orchestrator import ExtractOrchestrator


from getgather.browser.session import BrowserSession

from patchright.async_api import Page

from getgather.auth_flow import auth_flow, AuthFlowRequest, ExtractResult


async def auth(
    brand_id: BrandIdEnum,
    inputs: dict[str, str] = {},
    current_page_spec_name: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:

    profile_id = SessionManager.get_browser_profile_id(
        session_id=session_id)

    auth_request = AuthFlowRequest(
        profile_id=profile_id,
        state=FlowState(
            inputs=inputs, current_page_spec_name=current_page_spec_name),
        extract=False,
    )
    auth_response = await auth_flow(brand_id, auth_request)
    if auth_response.state.finished:
        SessionManager.update_connected_brand(
            brand_id=brand_id, session_id=session_id)
        return {
            "status": auth_response.status,
        }
    else:
        return {
            "current_page_spec_name":  auth_response.state.current_page_spec_name,
            "prompt": auth_response.state.prompt,
            "status": auth_response.status,
            "error": auth_response.state.error
        }


async def extract(
    brand_id: BrandIdEnum,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Extract data from a brand."""

    profile_id = SessionManager.get_browser_profile_id(
        session_id=session_id)
    browser_profile = BrowserProfile.get(
        profile_id=profile_id
    )

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

    parsed_bundles = [
        bundle for bundle in extract_result.bundles if bundle.parsed]
    return {
        "extract_result": parsed_bundles if parsed_bundles else extract_result.bundles,
    }


async def start_browser_session(
    session_id: str | None = None,
) -> Page:

    profile_id = SessionManager.get_browser_profile_id(
        session_id=session_id)
    browser_profile = BrowserProfile.get(
        profile_id=profile_id
    )

    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()
    return await browser_session.page()
