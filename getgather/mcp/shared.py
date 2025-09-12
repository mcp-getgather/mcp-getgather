"""Simplified shared functions using global profile manager."""

import asyncio
import functools
import time
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

import httpx
from fastmcp import Context
from fastmcp.server.dependencies import get_context, get_http_headers

from getgather.api.routes.link.types import HostedLinkTokenRequest
from getgather.browser.session import BrowserSession
from getgather.connectors.spec_loader import BrandIdEnum
from getgather.extract_orchestrator import ExtractOrchestrator
from getgather.logs import logger
from getgather.mcp.connection_manager import connection_manager
from getgather.mcp.profile_manager import global_profile_manager
from getgather.signin_flow import ExtractResult


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    allowed = {
        "host",
        "x-forwarded-proto", 
        "x-forwarded-host",
        "x-forwarded-port",
        "x-original-host",
        "x-scheme",
    }
    return {k: v for k, v in headers.items() if k.lower() in allowed}


async def signin_hosted_link(brand_id: BrandIdEnum) -> dict[str, Any]:
    """Auth with a link using global profile."""
    
    if connection_manager.is_connected(brand_id):
        return {
            "status": "FINISHED",
            "message": "Brand already connected.",
        }
    
    profile = global_profile_manager.get_profile()
    logger.info(
        "Creating link for brand", 
        extra={"brand_id": str(brand_id), "profile_id": profile.id}
    )
    
    request_data = HostedLinkTokenRequest(brand_id=str(brand_id), profile_id=profile.id)
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        headers = get_http_headers(include_all=True)
        sanitized = _sanitize_headers(headers)
        host = headers.get("host")
        scheme = headers.get("x-forwarded-proto", "http")
        base_url = f"{scheme}://{host}" if host else "http://localhost:23456"
        
        url = f"{base_url}/api/link/create"
        logger.info(
            "[signin_hosted_link] Creating hosted link",
            extra={"url": url, "host": host, "scheme": scheme, "headers": sanitized},
        )
        
        sanitized["Content-Type"] = "application/json"
        response = await client.post(url, headers=sanitized, json=request_data.model_dump())
        response_json = response.json()
        
        logger.info(
            "[signin_hosted_link] Hosted link created successfully",
            extra={
                "status_code": response.status_code,
                "request_url": str(response.request.url),
                "link_id": response_json.get("link_id"),
                "hosted_link_url": response_json.get("hosted_link_url"),
            },
        )
    
    return {
        "url": response_json["hosted_link_url"],
        "link_id": response_json["link_id"],
        "message": "Continue the sign in process in your browser. If you are not redirected, open the link url in your browser.",
        "system_message": (
            "Try open the url in a browser with a tool if available."
            " Give the url to the user so the user can open it manually in their browser."
            " Then call poll_signin tool with the link_id to check if the sign in is completed. "
            " Once the sign in is completed successfully, then call this tool again to proceed with the action."
        ),
    }


async def poll_status_hosted_link(context: Context, hosted_link_id: str) -> dict[str, Any]:
    """Poll sign in for a hosted link."""
    progress_count = 0
    async with httpx.AsyncClient(follow_redirects=True) as client:
        timeout_seconds = 120
        start_time = time.monotonic()
        processing = True
        
        while processing:
            if time.monotonic() - start_time >= timeout_seconds:
                logger.warning(
                    "[poll_status_hosted_link] Timed out polling link status",
                    extra={"hosted_link_id": hosted_link_id, "timeout_seconds": timeout_seconds},
                )
                return {
                    "status": "ERROR", 
                    "message": f"Sign in timed out after {timeout_seconds} seconds. Please try again.",
                }
            
            headers = get_http_headers(include_all=True)
            sanitized = _sanitize_headers(headers)
            host = headers.get("host")
            scheme = headers.get("x-forwarded-proto", "http")
            base_url = f"{scheme}://{host}" if host else "http://localhost:23456"
            
            url = f"{base_url}/api/link/status/{hosted_link_id}"
            logger.info(
                "[poll_status_hosted_link] Polling link status",
                extra={"url": url, "host": host, "scheme": scheme, "headers": sanitized},
            )
            
            response = await client.get(url)
            logger.info(
                "[poll_status_hosted_link] Response status",
                extra={"status_code": response.status_code, "url": response.request.url},
            )
            
            if response.status_code == 404:
                return {
                    "status": "ERROR",
                    "message": f"Link '{hosted_link_id}' not found or expired",
                }
            
            response_json = response.json()
            logger.info(
                "[poll_status_hosted_link] Received status response",
                extra={
                    "status_code": response.status_code,
                    "request_url": str(response.request.url),
                    "status": response_json.get("status"),
                    "response_message": response_json.get("message"),
                },
            )
            
            if response_json["status"] == "completed":
                processing = False
                brand_id = BrandIdEnum(response_json["brand_id"])
                connection_manager.set_connected(brand_id, True)
                logger.info(
                    "[poll_status_hosted_link] Marked brand as connected",
                    extra={"brand_id": str(brand_id)},
                )
            
            progress_count += 1
            await context.report_progress(progress=progress_count, message=response_json["message"])
            await asyncio.sleep(1)
            
        return {
            "status": "FINISHED",
            "message": "Sign in completed successfully.",
        }


def get_mcp_brand_id() -> BrandIdEnum:
    """Get the brand ID from the mcp context."""
    brand_id = get_context().get_state("brand_id")
    if not brand_id:
        raise ValueError("Brand ID is not set")
    return brand_id


def get_global_browser_session() -> BrowserSession:
    """Get the global browser session from context."""
    session = get_context().get_state("browser_session")
    if not session:
        raise ValueError("Browser session is not set")
    return session


P = ParamSpec("P")
T = TypeVar("T")


def with_global_browser_session(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Run a function with the global browser session."""
    
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        browser_session = global_profile_manager.get_session()
        
        mcp_ctx = get_context()
        mcp_ctx.set_state("browser_session", browser_session)
        
        await browser_session.start()
        try:
            return await func(*args, **kwargs)
        finally:
            await browser_session.stop()
            mcp_ctx.set_state("browser_session", None)
    
    return wrapper


@with_global_browser_session
async def extract() -> dict[str, Any]:
    """Extract data from a brand using global profile."""
    browser_session = get_global_browser_session()
    brand_id = get_mcp_brand_id()
    
    extract_orchestrator = ExtractOrchestrator(
        brand_id=brand_id,
        browser_profile=browser_session.profile,
        nested_browser_session=True,
    )
    await extract_orchestrator.extract_flow()
    extract_result = ExtractResult(
        profile_id=browser_session.profile.id,
        state=extract_orchestrator.state,
        bundles=extract_orchestrator.bundles,
    )
    
    parsed_bundles = [bundle for bundle in extract_result.bundles if bundle.parsed]
    return {
        "extract_result": parsed_bundles if parsed_bundles else extract_result.bundles,
    }