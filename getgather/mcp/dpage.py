import asyncio
import ipaddress
import logging
import os
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup, Tag
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastmcp.server.dependencies import get_http_headers
from nanoid import generate
from patchright.async_api import Page

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.config import settings
from getgather.distill import (
    Match,
    autoclick,
    capture_page_artifacts,
    convert,
    distill,
    get_selector,
    load_distillation_patterns,
    report_distill_error,
    run_distillation_loop,
    terminate,
)
from getgather.logs import logger
from getgather.mcp.html_renderer import render_form

router = APIRouter(prefix="/dpage", tags=["dpage"])


active_pages: dict[str, Page] = {}
distillation_results: dict[str, str | list[dict[str, str | list[str]]]] = {}
pending_callbacks: dict[str, dict[str, Any]] = {}  # Store callbacks to resume after signin
global_browser_profile: BrowserProfile | None = None


async def dpage_add(
    browser_profile: BrowserProfile | None = None,
    location: str | None = None,
    id: str | None = None,
):
    if id is None:
        FRIENDLY_CHARS: str = "23456789abcdefghijkmnpqrstuvwxyz"
        id = generate(FRIENDLY_CHARS, 8)
        if settings.HOSTNAME:
            id = f"{settings.HOSTNAME}-{id}"

    if browser_profile is None:
        browser_profile = BrowserProfile()

    session = BrowserSession.get(browser_profile)

    session = await session.start()
    page = await session.context.new_page()

    try:
        if location:
            if not location.startswith("http"):
                location = f"https://{location}"
            await page.goto(location, timeout=settings.BROWSER_TIMEOUT)
    except Exception as error:
        hostname = (
            urllib.parse.urlparse(location).hostname if location else "unknown"
        ) or "unknown"
        await report_distill_error(
            error=error,
            page=page,
            profile_id=browser_profile.id,
            location=location if location else "unknown",
            hostname=hostname,
            iteration=0,
        )
    active_pages[id] = page
    return id


async def dpage_close(id: str) -> None:
    if id in active_pages:
        await active_pages[id].close()
        del active_pages[id]


async def dpage_check(id: str):
    TICK = 1  # seconds
    TIMEOUT = 120  # seconds
    max = TIMEOUT // TICK

    for iteration in range(max):
        logger.debug(f"Checking dpage {id}: {iteration + 1} of {max}")
        await asyncio.sleep(TICK)

        # Check if signin completed
        if id in distillation_results:
            return distillation_results[id]

    return None


def render(content: str, options: dict[str, str] | None = None) -> str:
    """Render HTML template with content and options."""
    if options is None:
        options = {}

    title = options.get("title", "GetGather")
    action = options.get("action", "")

    return render_form(content, title, action)


# Since the browser can't redirect from GET to POST,
# we'll use an auto-submit form to do that.
def redirect(id: str) -> HTMLResponse:
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <body>
      <form id="redirect" action="/dpage/{id}" method="post">
      </form>
      <script>document.getElementById('redirect').submit();</script>
    </body>
    </html>
    """)


@router.get("", response_class=HTMLResponse)
@router.get("/{id}", response_class=HTMLResponse)
async def get_dpage(location: str | None = None, id: str | None = None) -> HTMLResponse:
    if id:
        if id in active_pages:
            return redirect(id)
        raise HTTPException(status_code=404, detail="Invalid page id")

    if not location:
        raise HTTPException(status_code=400, detail="Missing location parameter")

    logger.info(f"Starting distillation at {location}...")
    id = await dpage_add(location=location)
    return redirect(id)


FINISHED_MSG = "Finished! You can close this window now."


@router.post("/{id}", response_class=HTMLResponse)
async def post_dpage(id: str, request: Request) -> HTMLResponse:
    if id not in active_pages:
        raise HTTPException(status_code=404, detail="Page not found")

    page = active_pages[id]

    form_data = await request.form()
    fields: dict[str, str] = {k: str(v) for k, v in form_data.items()}

    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    logger.info(f"Continuing distillation for page {id}...")
    logger.debug(f"Available distillation patterns: {len(patterns)}")

    TICK = 1  # seconds
    TIMEOUT = 15  # seconds
    max = TIMEOUT // TICK

    current = Match(name="", priority=-1, distilled="")

    if logger.isEnabledFor(logging.DEBUG):
        await capture_page_artifacts(page, identifier=id, prefix="dpage_debug")

    for iteration in range(max):
        logger.debug(f"Iteration {iteration + 1} of {max}")
        await asyncio.sleep(TICK)

        location = page.url
        hostname = urllib.parse.urlparse(location).hostname

        match = await distill(hostname, page, patterns)
        if not match:
            logger.info("No matched pattern found")
            continue

        if match.distilled == current.distilled:
            logger.info(f"Still the same: {match.name}")
            continue

        current = match
        distilled = match.distilled

        print(distilled)

        title_element = BeautifulSoup(distilled, "html.parser").find("title")
        title = title_element.get_text() if title_element is not None else "GetGather"
        action = f"/dpage/{id}"
        options = {"title": title, "action": action}

        if await terminate(page, distilled):
            logger.info("Finished!")
            converted = await convert(distilled)

            if id in pending_callbacks:
                callback_info = pending_callbacks[id]
                logger.info(f"Signin completed for {id}, resuming callback...")

                callback_result = await dpage_mcp_tool(
                    initial_url=callback_info["initial_url"],
                    result_key=callback_info["result_key"],
                    timeout=callback_info["timeout"],
                    callback=callback_info["callback"],
                    signin_completed=True,
                    page_id=callback_info["page_id"],
                )

                if callback_info["result_key"] in callback_result:
                    distillation_results[id] = callback_result[callback_info["result_key"]]
                else:
                    logger.error(
                        f"Result key '{callback_info['result_key']}' not found in callback_result"
                    )
                    distillation_results[id] = "Error: Result key not found"

                del pending_callbacks[id]
                await dpage_close(id)
                return HTMLResponse(render(FINISHED_MSG, options))

            await dpage_close(id)
            if converted:
                print(converted)
                distillation_results[id] = converted
            else:
                logger.info("No conversion found")
                distillation_results[id] = distilled
            return HTMLResponse(render(FINISHED_MSG, options))

        names: list[str] = []
        document = BeautifulSoup(distilled, "html.parser")
        inputs = document.find_all("input")

        for input in inputs:
            if isinstance(input, Tag):
                gg_match = input.get("gg-match")
                selector, frame_selector = get_selector(
                    str(gg_match) if gg_match is not None else ""
                )
                name = input.get("name")
                input_type = input.get("type")

                if selector:
                    if input_type == "checkbox":
                        if not name:
                            logger.warning(f"No name for the checkbox {selector}")
                            continue
                        value = fields.get(str(name))
                        checked = value and len(str(value)) > 0
                        names.append(str(name))
                        logger.info(f"Status of checkbox {name}={checked}")
                        if checked:
                            if frame_selector:
                                await (
                                    page.frame_locator(str(frame_selector))
                                    .locator(str(selector))
                                    .check()
                                )
                            else:
                                await page.check(str(selector))
                    elif input_type == "radio":
                        if name is not None:
                            name_str = str(name)
                            value = fields.get(name_str)
                            if not value or len(value) == 0:
                                logger.warning(f"No form data found for radio button group {name}")
                                continue
                            radio = document.find("input", {"type": "radio", "id": str(value)})
                            if not radio or not isinstance(radio, Tag):
                                logger.warning(f"No radio button found with id {value}")
                                continue
                            logger.info(f"Handling radio button group {name}")
                            logger.info(f"Using form data {name}={value}")
                            radio_selector, radio_frame_selector = get_selector(
                                str(radio.get("gg-match"))
                            )
                            if radio_frame_selector:
                                await (
                                    page.frame_locator(str(radio_frame_selector))
                                    .locator(str(radio_selector))
                                    .check()
                                )
                            else:
                                await page.check(str(radio_selector))
                            radio["checked"] = "checked"
                            current.distilled = str(document)
                            names.append(str(input.get("id")) if input.get("id") else "radio")
                            await asyncio.sleep(0.25)
                    elif name is not None:
                        name_str = str(name)
                        value = fields.get(name_str)
                        if value and len(value) > 0:
                            logger.info(f"Using form data {name}")
                            names.append(name_str)
                            input["value"] = value
                            current.distilled = str(document)
                            if frame_selector:
                                await (
                                    page.frame_locator(str(frame_selector))
                                    .locator(str(selector))
                                    .fill(value)
                                )
                            else:
                                await page.fill(str(selector), value)
                            del fields[name_str]
                            await asyncio.sleep(0.25)
                        else:
                            logger.info(f"No form data found for {name}")

        await autoclick(page, distilled, "[gg-autoclick]:not(button)")
        SUBMIT_BUTTON = "button[gg-autoclick], button[type=submit]"
        if document.select(SUBMIT_BUTTON):
            if len(names) > 0 and len(inputs) == len(names):
                logger.info("Submitting form, all fields are filled...")
                await autoclick(page, distilled, SUBMIT_BUTTON)
                continue
            logger.warning("Not all form fields are filled")
            return HTMLResponse(render(str(document.find("body")), options))

    raise HTTPException(status_code=503, detail="Timeout reached")


def is_local_address(host: str) -> bool:
    hostname = host.split(":")[0].lower().strip()
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_loopback
    except ValueError:
        return hostname in ("localhost", "127.0.0.1")


async def dpage_mcp_tool(
    initial_url: str,
    result_key: str,
    timeout: int = 2,
    callback: Any = None,
    signin_completed: bool = False,
    page_id: str | None = None,
) -> dict[str, Any]:
    """
    Generic MCP tool that supports both pattern-based distillation and manual browser control.

    Args:
        initial_url: URL to navigate to
        result_key: Key name for the result in return dict
        timeout: Timeout in seconds
        callback: Optional async function for manual browser control.
                 If provided, skips pattern matching and goes straight to manual control.

    Returns:
        Dict with result or signin flow info
    """
    headers = get_http_headers(include_all=True)
    incognito = headers.get("x-incognito", "0") == "1"

    if incognito:
        browser_profile = BrowserProfile()
    else:
        global global_browser_profile
        if global_browser_profile is None:
            logger.info(f"Creating global browser profile...")
            global_browser_profile = BrowserProfile()
            session = BrowserSession.get(global_browser_profile)
            session = await session.start()
            init_page = await session.new_page()  # never use old pages in global session due to really difficult race conditions with concurrent requests
            try:
                await init_page.goto(initial_url)
            except Exception as e:
                await report_distill_error(
                    error=e,
                    page=init_page,
                    profile_id=global_browser_profile.id,
                    location=initial_url,
                    hostname=urllib.parse.urlparse(initial_url).hostname or "",
                    iteration=0,
                )
            await asyncio.sleep(1)

        browser_profile = global_browser_profile

    # If callback is provided and signin is completed, skip patterns and go straight to manual control
    if callback is not None and signin_completed and page_id is not None:
        if page_id not in active_pages:
            logger.error(f"Page ID {page_id} not found in active_pages")
            return {result_key: None, "error": f"Page ID {page_id} not found"}

        try:
            page = active_pages[page_id]
            await page.goto(initial_url)
            result = await callback(page)
            return {result_key: result}
        except Exception as e:
            logger.error(f"Callback execution failed: {e}")
            return {result_key: None, "error": str(e)}

    # For callbacks, try with existing global session if available first
    if callback is not None and global_browser_profile is not None:
        try:
            logger.info("Trying callback with existing global browser session...")
            session = BrowserSession.get(global_browser_profile)
            await session.start()
            page = await session.page()
            await page.goto(initial_url)
            result = await callback(page)
            logger.info("Callback succeeded with existing session!")
            return {result_key: result}
        except Exception as e:
            logger.info(f"Callback with existing session failed: {e}, proceeding with signin flow")

    # If no callback or callback failed, try pattern-based distillation
    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)
    distillation_result, terminated = await run_distillation_loop(
        initial_url,
        patterns,
        browser_profile=browser_profile,
        interactive=False,
        timeout=timeout,
        stop_ok=False,  # Keep global session alive
    )
    if terminated:
        return {result_key: distillation_result}

    # Fall back to interactive signin flow
    id = await dpage_add(browser_profile=browser_profile, location=initial_url)

    # Store callback for auto-resumption after signin
    if callback is not None:
        pending_callbacks[id] = {
            "callback": callback,
            "initial_url": initial_url,
            "result_key": result_key,
            "timeout": timeout,
            "page_id": id,
        }

    host = headers.get("x-forwarded-host") or headers.get("host")
    if host is None:
        logger.warning("Missing Host header; defaulting to localhost")
        base_url = "http://localhost:23456"
    else:
        default_scheme = "http" if is_local_address(host) else "https"
        scheme = headers.get("x-forwarded-proto", default_scheme)
        base_url = f"{scheme}://{host}"

    url = f"{base_url}/dpage/{id}"
    logger.info(f"Continue with the sign in at {url}", extra={"url": url, "id": id})

    message = "Continue to sign in in your browser"

    return {
        "url": url,
        "message": f"{message} at {url}.",
        "signin_id": id,
        "system_message": (
            f"Try open the url {url} in a browser with a tool if available."
            "Give the url to the user so the user can open it manually in their browser."
            f"Then call check_signin tool with the signin_id to check if the sign in process is completed. "
        ),
    }
