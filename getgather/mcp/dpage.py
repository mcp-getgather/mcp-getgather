import asyncio
import ipaddress
import os
import urllib.parse
from asyncio import Task
from typing import Any

from bs4 import BeautifulSoup, Tag
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastmcp.server.dependencies import get_http_headers
from nanoid import generate
from patchright.async_api import Page, Route

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.config import settings
from getgather.distill import (
    Match,
    autoclick,
    convert,
    distill,
    get_selector,
    load_distillation_patterns,
    run_distillation_loop,
    terminate,
)
from getgather.logs import logger

router = APIRouter(prefix="/dpage", tags=["dpage"])


def block_unwanted_resources(route: Route) -> Task[None]:
    """Block images, media (videos), and fonts"""
    return asyncio.create_task(
        route.abort()
        if route.request.resource_type in ["image", "media", "font"]
        else route.continue_()
    )


active_pages: dict[str, Page] = {}
distillation_results: dict[str, str | list[dict[str, str | list[str]]]] = {}
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

    session = BrowserSession(browser_profile.id)

    await session.start()
    page = await session.context.new_page()
    await page.route("**/*", block_unwanted_resources)

    if location:
        if not location.startswith("http"):
            location = f"https://{location}"
        await page.goto(location, timeout=300000)

    active_pages[id] = page
    return id


async def dpage_close(id: str) -> None:
    if id in active_pages:
        # await active_pages[id].close()
        del active_pages[id]


async def dpage_check(id: str):
    TICK = 1  # seconds
    TIMEOUT = 120  # seconds
    max = TIMEOUT // TICK

    for iteration in range(max):
        logger.debug(f"Checking dpage {id}: {iteration + 1} of {max}")
        await asyncio.sleep(TICK)
        if id in distillation_results:
            return distillation_results[id]

    return None


def render(content: str, options: dict[str, str] | None = None) -> str:
    if options is None:
        options = {}

    title = options.get("title", "GetGather")
    action = options.get("action", "")

    return f"""<!doctype html>
<html data-theme=light>
  <head>
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  </head>
  <body>
    <main class="container">
      <section>
        <h2>{title}</h2>
        <articles>
        <form method="POST" action="{action}">
        {content}
        </form>
        </articles>
      </section>
    </main>
  </body>
</html>"""


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

    current = Match(name="", priority=-1, distilled="", matches=[])

    for iteration in range(max):
        logger.debug(f"Iteration {iteration + 1} of {max}")
        await asyncio.sleep(TICK)

        hostname = urllib.parse.urlparse(page.url).hostname

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

        title_element = document.find("title")
        title = title_element.get_text() if title_element is not None else "GetGather"
        action = f"/dpage/{id}"
        options = {"title": title, "action": action}

        if len(inputs) == len(names):
            await autoclick(page, distilled)
            if await terminate(page, distilled):
                logger.info("Finished!")
                converted = await convert(distilled)
                await dpage_close(id)
                if converted:
                    print(converted)
                    distillation_results[id] = converted
                else:
                    logger.info("No conversion found")
                    distillation_results[id] = distilled
                return HTMLResponse(render(FINISHED_MSG, options))

            logger.info("All form fields are filled")
            continue

        if await terminate(page, distilled):
            converted = await convert(distilled)
            await dpage_close(id)
            if converted:
                print(converted)
                distillation_results[id] = converted
            return HTMLResponse(render(FINISHED_MSG, options))
        else:
            logger.info("Not all form fields are filled")

        return HTMLResponse(render(str(document.find("body")), options))

    raise HTTPException(status_code=503, detail="Timeout reached")


def is_local_address(host: str) -> bool:
    hostname = host.split(":")[0].lower().strip()
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_loopback
    except ValueError:
        return hostname in ("localhost", "127.0.0.1")


async def dpage_mcp_tool(initial_url: str, result_key: str, timeout: int = 2) -> dict[str, Any]:
    """Generic MCP tool based on distillation"""

    path = os.path.join(os.path.dirname(__file__), "patterns", "**/*.html")
    patterns = load_distillation_patterns(path)

    headers = get_http_headers(include_all=True)
    incognito = headers.get("x-incognito", "0") == "1"

    if incognito:
        browser_profile = BrowserProfile()
    else:
        global global_browser_profile
        if global_browser_profile is None:
            logger.info(f"Creating global browser profile...")
            global_browser_profile = BrowserProfile()
            session = BrowserSession(global_browser_profile.id)
            await session.start()
            logger.debug("Visiting google.com to initialize the profile...")

            # to help troubleshooting
            debug_page = await session.context.new_page()
            await debug_page.goto("https://ifconfig.me")

            init_page = await session.context.new_page()
            await init_page.route("**/*", block_unwanted_resources)

            await init_page.goto(initial_url)
            await asyncio.sleep(1)

        browser_profile = global_browser_profile

    # First, try without any interaction as this will work if the user signed in previously
    distillation_result = await run_distillation_loop(
        initial_url,
        patterns,
        browser_profile=browser_profile,
        interactive=False,
        timeout=timeout,
        with_terminate_flag=True,
    )
    if isinstance(distillation_result, dict) and distillation_result["terminated"]:
        return {result_key: distillation_result["result"]}

    # If that didn't work, try signing in via distillation
    id = await dpage_add(browser_profile=browser_profile, location=initial_url)

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
    return {
        "url": url,
        "message": f"Continue to sign in in your browser at {url}.",
        "signin_id": id,
        "system_message": (
            f"Try open the url {url} in a browser with a tool if available."
            "Give the url to the user so the user can open it manually in their browser."
            "Then call check_signin tool with the signin_id to check if the sign in process is completed. "
            "Once it is completed successfully, then call this tool again to proceed with the action."
        ),
    }
