#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
import urllib.parse
from glob import glob
from typing import cast

import pwinput
from bs4 import BeautifulSoup
from bs4.element import Tag
from patchright.async_api import Page

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.config import settings
from getgather.distill import Pattern, distill
from getgather.logs import logger

_ = settings.LOG_LEVEL


async def sleep(seconds: float):
    await asyncio.sleep(seconds)


async def ask(message: str, mask: str | None = None) -> str:
    if mask:
        return pwinput.pwinput(f"{message}: ", mask=mask)
    else:
        return input(f"{message}: ")


async def click(
    page: Page, selector: str, timeout: int = 3000, frame_selector: str | None = None
) -> None:
    LOCATOR_ALL_TIMEOUT = 100
    if frame_selector:
        locator = page.frame_locator(str(frame_selector)).locator(str(selector))
    else:
        locator = page.locator(str(selector))
    try:
        elements = await locator.all()
        logger.debug(f'Found {len(elements)} elements for selector "{selector}"')
        for element in elements:
            logger.debug(f"Checking {element}")
            if await element.is_visible():
                logger.debug(f"Clicking on {element}")
                try:
                    await element.click()
                    return
                except Exception as err:
                    logger.warning(f"Failed to click on {selector} {element}: {err}")
    except Exception as e:
        if timeout > 0 and "TimeoutError" in str(type(e)):
            logger.warning(f"retrying click {selector} {timeout}")
            await click(page, selector, timeout - LOCATOR_ALL_TIMEOUT, frame_selector)
            return
        logger.error(f"Failed to click on {selector}: {e}")
        raise e


def parse(html: str):
    return BeautifulSoup(html, "html.parser")


def load_patterns() -> list[Pattern]:
    patterns: list[Pattern] = []
    for name in glob("./getgather/connectors/brand_specs/**/*.html", recursive=True):
        with open(name, "r", encoding="utf-8") as f:
            content = f.read()
        patterns.append(Pattern(name=name, pattern=parse(content)))
    return patterns


async def autofill(page: Page, distilled: str, fields: list[str]):
    document = parse(distilled)
    root = document.find("html")
    domain = None
    if root:
        domain = cast(Tag, root).get("gg-domain")

    for field in fields:
        element = document.find("input", {"type": field})
        selector = None
        frame_selector = None

        if element:
            selector = cast(Tag, element).get("gg-match")
            frame_selector = cast(Tag, element).get("gg-frame")

        if selector:
            source = f"{domain}_{field}" if domain else field
            key = source.upper()
            value = os.getenv(key)

            if value and len(value) > 0:
                logger.info(f"Using {key} for {field}")

                if frame_selector:
                    await page.frame_locator(str(frame_selector)).locator(str(selector)).fill(value)
                else:
                    await page.fill(str(selector), value)
            else:
                placeholder = cast(Tag, element).get("placeholder")
                prompt = str(placeholder) if placeholder else f"Please enter {field}"
                mask = "*" if field == "password" else None

                if frame_selector:
                    await (
                        page.frame_locator(str(frame_selector))
                        .locator(str(selector))
                        .fill(await ask(prompt, mask))
                    )

                else:
                    await page.fill(str(selector), await ask(prompt, mask))
            await sleep(0.25)


async def autoclick(page: Page, distilled: str):
    document = parse(distilled)
    buttons = document.find_all(attrs={"gg-autoclick": True})

    for button in buttons:
        if isinstance(button, Tag):
            selector = button.get("gg-match")
            if selector:
                logger.info(f"Auto-clicking {selector}")
                frame_selector = button.get("gg-frame")
                if isinstance(frame_selector, list):
                    frame_selector = frame_selector[0] if frame_selector else None
                await click(page, str(selector), frame_selector=frame_selector)


async def terminate(page: Page, distilled: str) -> bool:
    document = parse(distilled)
    stops = document.find_all(attrs={"gg-stop": True})
    if len(stops) > 0:
        logger.info("Found stop elements, terminating session...")
        return True
    return False


async def list_command():
    spec_files = glob("./getgather/connectors/brand_specs/**/*", recursive=True)
    spec_files = [f for f in spec_files if f.endswith(".html")]

    for name in spec_files:
        logger.info(os.path.basename(name))


async def distill_command(location: str, option: str | None = None):
    patterns = load_patterns()

    logger.info(f"Distilling {location}")

    profile = BrowserProfile()
    async with browser_session(profile) as session:
        page = await session.page()

        if location.startswith("http"):
            hostname = urllib.parse.urlparse(location).hostname
            await page.goto(location)
        else:
            hostname = option or ""
            with open(location, "r", encoding="utf-8") as f:
                content = f.read()
            await page.set_content(content)

        match = await distill(hostname, page, patterns)

        if match:
            print()
            print(match.distilled)
            print()


async def run_command(location: str):
    if not location.startswith("http"):
        location = f"https://{location}"

    hostname = urllib.parse.urlparse(location).hostname or ""
    patterns = load_patterns()

    profile = BrowserProfile()
    async with browser_session(profile) as session:
        page = await session.page()

        logger.info(f"Starting browser {profile.id}")
        logger.info(f"Navigating to {location}")
        await page.goto(location)

        TICK = 1  # seconds
        TIMEOUT = 15  # seconds
        max = TIMEOUT // TICK

        current = {"name": None, "distilled": None}

        for iteration in range(max):
            logger.info("")
            logger.info(f"Iteration {iteration + 1} of {max}")
            await sleep(TICK)

            match = await distill(hostname, page, patterns)
            if match:
                name = match.name
                distilled = match.distilled

                if distilled == current.get("distilled"):
                    logger.debug(f"Still the same: {name}")
                else:
                    current = {"name": name, "distilled": distilled}
                    print()
                    print(distilled)
                    await autofill(page, distilled, ["email", "password", "tel", "text"])
                    await autoclick(page, distilled)

                    if await terminate(page, distilled):
                        break
            else:
                logger.debug(f"No matched pattern found")

        logger.info("")
        logger.info(f"Terminating browser {profile.id}")
        logger.info("Terminated.")


async def inspect_command(id: str, option: str | None = None):
    profile = BrowserProfile(id=id)
    async with browser_session(profile) as session:
        page = await session.page()

        if option and len(option) > 0:
            url = option if option.startswith("http") else f"https://{option}"
            await page.goto(url)
        else:
            await page.goto("https://google.com")

        await ask("Press Enter to terminate session")


async def main():
    if len(sys.argv) == 1:
        return "server"

    parser = argparse.ArgumentParser(description="MIDDLEMAN")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("list", help="List all patterns")

    distill_parser = subparsers.add_parser("distill", help="Distill a webpage")
    distill_parser.add_argument("parameter", help="URL or file path")
    distill_parser.add_argument("option", nargs="?", help="Hostname for file distillation")

    run_parser = subparsers.add_parser("run", help="Run automation")
    run_parser.add_argument("parameter", help="URL or domain")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect browser session")
    inspect_parser.add_argument("parameter", help="Browser ID")
    inspect_parser.add_argument("option", nargs="?", help="URL to navigate to")

    subparsers.add_parser("server", help="Start web server")

    args = parser.parse_args()

    if args.command == "list":
        await list_command()
    elif args.command == "distill":
        await distill_command(args.parameter, args.option)
    elif args.command == "run":
        await run_command(args.parameter)
    elif args.command == "inspect":
        await inspect_command(args.parameter, args.option)
    elif args.command == "server":
        return "server"
    else:
        parser.print_help()


if __name__ == "__main__":
    result = asyncio.run(main())
    if result == "server":
        logger.info("TODO: launch MCP server")
