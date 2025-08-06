import asyncio
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Context
from fastmcp.server.dependencies import get_http_headers

from getgather.api.routes.link.types import HostedLinkTokenRequest
from getgather.auth_flow import ExtractResult
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.config import settings
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.extract_orchestrator import ExtractOrchestrator
from getgather.logs import logger
from getgather.mcp.session_manager import SessionManager


async def auth_hosted_link(brand_id: BrandIdEnum, session_id: str | None = None) -> dict[str, Any]:
    """Auth with a link."""

    if SessionManager.is_brand_connected(brand_id=brand_id, session_id=session_id):
        return {
            "status": "FINISHED",
            "message": "Brand already connected.",
        }

    profile_id = SessionManager.get_browser_profile_id(session_id=session_id)
    logger.info(f"Creating link for brand {brand_id} and profile {profile_id}")

    request_data = HostedLinkTokenRequest(brand_id=str(brand_id), profile_id=profile_id)

    async with httpx.AsyncClient() as client:
        headers = get_http_headers(include_all=True)
        host = headers.get("host")
        response = await client.post(
            f"http://{host}/link/create",
            headers={"Content-Type": "application/json"},
            json=request_data.model_dump(),
        )

        logger.info(f"Response: {response.text}")
        response_json = response.json()

    open_url_msg = "Call open_url tool (if available) to open the link in your browser. "

    # verify that HOST_URL_OPENER is mounted
    if settings.HOST_URL_OPENER and Path(settings.HOST_URL_OPENER).exists():
        logger.info("Opening hosted link in browser at host")
        try:
            with open(Path(settings.HOST_URL_OPENER) / "url", "w") as f:
                f.write(response_json["hosted_link_url"] + "\n")
            open_url_msg = ""
        except Exception as e:
            logger.error(f"Error opening hosted link in browser: {e}")

    return {
        "url": response_json["hosted_link_url"],
        "session_id": response_json["session_id"],
        "message": "Continue the auth process in your browser. If you are not redirected, open the link in your browser.",
        "system_message": f"{open_url_msg}Give the url to the user so user can open it in their browser. Then call poll_auth tool to check if the auth is completed with the session_id. Then call this tool again to get the data.",
    }


async def poll_status_hosted_link(
    context: Context, hosted_link_session_id: str, session_id: str | None = None
) -> dict[str, Any]:
    """Poll auth for a session."""
    progress_count = 0
    async with httpx.AsyncClient() as client:
        processing = True
        while processing:
            headers = get_http_headers(include_all=True)
            host = headers.get("host")
            response = await client.get(
                f"http://{host}/link/status/{hosted_link_session_id}",
            )
            logger.info(f"Response: {response.text}")
            response_json = response.json()
            if response_json["status"] == "completed":
                processing = False
                SessionManager.update_connected_brand(
                    brand_id=response_json["brand_id"], session_id=session_id
                )

            progress_count += 1
            await context.report_progress(progress=progress_count, message=response_json["message"])

            await asyncio.sleep(1)
        return {
            "status": "FINISHED",
            "message": "Auth completed successfully.",
        }


async def extract(
    brand_id: BrandIdEnum,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Extract data from a brand."""
    browser_session = await start_browser_session(session_id=session_id)

    extract_orchestrator = ExtractOrchestrator(
        brand_id=brand_id,
        browser_profile=browser_session.profile,
        nested_browser_session=True,
    )
    await extract_orchestrator.extract_flow()
    await browser_session.stop()
    extract_result = ExtractResult(
        profile_id=browser_session.profile.profile_id,
        state=extract_orchestrator.state,
        bundles=extract_orchestrator.bundles,
    )

    parsed_bundles = [bundle for bundle in extract_result.bundles if bundle.parsed]
    return {
        "extract_result": parsed_bundles if parsed_bundles else extract_result.bundles,
    }


async def start_browser_session(
    session_id: str | None = None,
) -> BrowserSession:
    """Start a browser session and return the page object."""
    profile_id = SessionManager.get_browser_profile_id(session_id=session_id)
    browser_profile = BrowserProfile.get(profile_id=profile_id)

    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()
    return browser_session


async def stop_browser_session(
    session_id: str | None = None,
) -> None:
    profile_id = SessionManager.get_browser_profile_id(session_id=session_id)
    browser_profile = BrowserProfile.get(profile_id=profile_id)
    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.stop()
