import asyncio
from typing import Any

import httpx
from fastmcp import Context
from fastmcp.server.dependencies import get_http_headers

from getgather.api.routes.link.types import HostedLinkTokenRequest
from getgather.auth_flow import ExtractResult
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.database.repositories.brand_state_repository import BrandState
from getgather.extract_orchestrator import ExtractOrchestrator
from getgather.logs import logger


async def auth_hosted_link(brand_id: BrandIdEnum) -> dict[str, Any]:
    """Auth with a link."""

    if BrandState.is_brand_connected(brand_id):
        return {
            "status": "FINISHED",
            "message": "Brand already connected.",
        }

    profile_id = BrandState.get_browser_profile_id(brand_id)
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

    return {
        "url": response_json["hosted_link_url"],
        "link_id": response_json["link_id"],
        "message": "Continue the auth process in your browser. If you are not redirected, open the link url in your browser.",
        "system_message": (
            "Try open the url in a browser with a tool if available."
            " Give the url to the user so the user can open it manually in their browser."
            " Then call poll_auth tool with the link_id to check if the auth is completed. "
            " Once the auth is completed successfully, then call this tool again to proceed with the action."
        ),
    }


async def poll_status_hosted_link(context: Context, hosted_link_id: str) -> dict[str, Any]:
    """Poll auth for a hosted link."""
    progress_count = 0
    async with httpx.AsyncClient() as client:
        processing = True
        while processing:
            headers = get_http_headers(include_all=True)
            host = headers.get("host")
            response = await client.get(f"http://{host}/link/status/{hosted_link_id}")
            logger.info(f"Response: {response.text}")
            response_json = response.json()
            if response_json["status"] == "completed":
                processing = False
                BrandState.update_is_connected(
                    brand_id=BrandIdEnum(response_json["brand_id"]),
                    is_connected=True,
                )

            progress_count += 1
            await context.report_progress(progress=progress_count, message=response_json["message"])

            await asyncio.sleep(1)
        return {
            "status": "FINISHED",
            "message": "Auth completed successfully.",
        }


async def extract(brand_id: BrandIdEnum) -> dict[str, Any]:
    """Extract data from a brand."""
    browser_session = await start_browser_session(brand_id=brand_id)

    extract_orchestrator = ExtractOrchestrator(
        brand_id=brand_id,
        browser_profile=browser_session.profile,
        nested_browser_session=True,
    )
    await extract_orchestrator.extract_flow()
    await browser_session.stop()
    extract_result = ExtractResult(
        profile_id=browser_session.profile.id,
        state=extract_orchestrator.state,
        bundles=extract_orchestrator.bundles,
    )

    parsed_bundles = [bundle for bundle in extract_result.bundles if bundle.parsed]
    return {
        "extract_result": parsed_bundles if parsed_bundles else extract_result.bundles,
    }


async def start_browser_session(brand_id: BrandIdEnum) -> BrowserSession:
    """Start a browser session and return the page object."""
    profile_id: str | None = None
    if BrandState.is_brand_connected(brand_id):
        profile_id = BrandState.get_browser_profile_id(brand_id)

    if profile_id:
        browser_profile = BrowserProfile(id=profile_id)
    else:
        # For public tools or unauthenticated brands, launch a fresh browser
        # profile without persisting anything to the store.
        browser_profile = BrowserProfile()

    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.start()
    # Don't start recording here - will be started just before extraction
    return browser_session


async def stop_browser_session(brand_id: BrandIdEnum) -> None:
    profile_id = BrandState.get_browser_profile_id(brand_id)
    if not profile_id:
        # Nothing to stop if a stored profile was never created for this brand.
        return None
    browser_profile = BrowserProfile(id=profile_id)
    browser_session = await BrowserSession.get(browser_profile)
    await browser_session.stop()
