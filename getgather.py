#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
import urllib.parse
from typing import Any, Optional, cast

import nanoid
import pwinput
from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, Field
from stagehand import Stagehand

from getgather.distill import Pattern
from getgather.logs import logger

FRIENDLY_CHARS = "23456789abcdefghijkmnpqrstuvwxyz"


async def sleep(seconds: float):
    await asyncio.sleep(seconds)


async def ask(message: str, mask: Optional[str] = None) -> str:
    if mask:
        return pwinput.pwinput(f"{message}: ", mask=mask)
    else:
        return input(f"{message}: ")


async def click(
    page: Any, selector: str, timeout: int = 3000, frame_selector: Optional[str] = None
) -> None:
    LOCATOR_ALL_TIMEOUT = 100

    # Access the underlying Playwright page from Stagehand
    playwright_page = getattr(page, "_page", page)

    if frame_selector:
        locator = playwright_page.frame_locator(str(frame_selector)).locator(str(selector))
    else:
        locator = playwright_page.locator(str(selector))

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


def search(directory: str) -> list[str]:
    results: list[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            results.append(os.path.join(root, file))
    return results


def parse(html: str):
    return BeautifulSoup(html, "html.parser")


class Handle(BaseModel):
    id: str = Field(min_length=1, description="Browser session identifier")
    hostname: str
    location: str
    stagehand: Stagehand
    page: Any  # LivePageProxy that acts like StagehandPage

    class Config:
        arbitrary_types_allowed = True


async def init(location: str = "", hostname: str = "") -> Handle:
    global stagehand_instance

    id = nanoid.generate(FRIENDLY_CHARS, 6)
    directory = f"data/profiles/{id}"

    if not stagehand_instance:
        # Initialize Stagehand with a persistent user data directory
        stagehand_instance = Stagehand(
            env="LOCAL",  # Use local environment instead of browserbase
            headless=False,
            local_browser_launch_options={"user_data_dir": directory, "headless": False},
        )
        await stagehand_instance.init()

    # Get the page from Stagehand
    page = stagehand_instance.page

    return Handle(
        id=id, hostname=hostname, location=location, stagehand=stagehand_instance, page=page
    )


def load_patterns() -> list[Pattern]:
    patterns: list[Pattern] = []
    for name in [f for f in search("./getgather/connectors/brand_specs") if f.endswith(".html")]:
        with open(name, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = parse(content)
        patterns.append(Pattern(name=name, pattern=pattern))
    return patterns


async def autofill(page: Any, distilled: str, fields: list[str]):
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

                # Use Stagehand's act method to fill the field
                if frame_selector:
                    await page.act(
                        f"fill the field with selector '{selector}' inside frame '{frame_selector}' with value '{value}'"
                    )
                else:
                    await page.act(
                        f"fill the field with selector '{selector}' with value '{value}'"
                    )
            else:
                placeholder = cast(Tag, element).get("placeholder")
                prompt = str(placeholder) if placeholder else f"Please enter {field}"
                mask = "*" if field == "password" else None
                user_input = await ask(prompt, mask)

                # Use Stagehand's act method to fill the field with user input
                if frame_selector:
                    await page.act(
                        f"fill the field with selector '{selector}' inside frame '{frame_selector}' with value '{user_input}'"
                    )
                else:
                    await page.act(
                        f"fill the field with selector '{selector}' with value '{user_input}'"
                    )
            await sleep(0.25)


async def autoclick(page: Any, distilled: str):
    document = parse(distilled)
    buttons = document.find_all(attrs={"gg-autoclick": True})

    for button in buttons:
        if isinstance(button, Tag):
            selector = button.get("gg-match")
            if selector:
                logger.info(f"Auto-clicking {selector}")
                frame_selector = button.get("gg-frame")
                await click(page, str(selector), frame_selector=str(frame_selector))


async def terminate(page: Any, distilled: str) -> bool:
    document = parse(distilled)
    stops = document.find_all(attrs={"gg-stop": True})
    if len(stops) > 0:
        logger.info("Found stop elements, terminating session...")
        return True
    return False


stagehand_instance: Stagehand | None = None


async def list_command():
    spec_files = search("./getgather/connectors/brand_specs")
    spec_files = [f for f in spec_files if f.endswith(".html")]

    for name in spec_files:
        logger.info(name.replace("specs/", ""))


async def distill_command(location: str, option: str | None = None):
    # patterns = load_patterns()  # TODO: Re-enable when distill is updated for Stagehand

    logger.info(f"Distilling {location}")

    # Initialize temporary Stagehand instance for distilling
    stagehand = Stagehand(
        env="LOCAL", headless=False, local_browser_launch_options={"headless": False}
    )
    await stagehand.init()

    try:
        page = stagehand.page
        if not page:
            raise RuntimeError("Stagehand page not available")

        if location.startswith("http"):
            # hostname = urllib.parse.urlparse(location).hostname  # TODO: Use when distill is re-enabled
            await page.goto(location)
        else:
            # hostname = option or ""  # TODO: Use when distill is re-enabled
            with open(location, "r", encoding="utf-8") as f:
                content = f.read()
            await page.set_content(content)

        # For now, we'll skip distill functionality as it requires patchright Page
        # TODO: Update distill function to work with Stagehand
        print(
            "Distill functionality temporarily disabled - need to update distill module for Stagehand"
        )
        match = None

        if match:
            print()
            print(match.distilled)
            print()
    finally:
        await stagehand.close()


async def run_command(location: str):
    if not location.startswith("http"):
        location = f"https://{location}"

    hostname = urllib.parse.urlparse(location).hostname or ""
    # patterns = load_patterns()  # TODO: Re-enable when distill is updated for Stagehand

    browser_data = await init(location, hostname)
    browser_id = browser_data.id
    stagehand = browser_data.stagehand
    page = browser_data.page

    logger.info(f"Starting browser {browser_id}")

    logger.info(f"Navigating to {location}")
    if not page:
        raise RuntimeError("Stagehand page not available")
    await page.goto(location)

    TICK = 1  # seconds
    TIMEOUT = 15  # seconds
    max = TIMEOUT // TICK

    current = {"name": None, "distilled": None}

    try:
        for iteration in range(max):
            logger.info("")
            logger.info(f"Iteration {iteration + 1} of {max}")
            await sleep(TICK)

            # TODO: Update distill function to work with Stagehand
            # match = await distill(hostname, page, patterns)
            match = None  # Temporarily disabled
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
        logger.info(f"Terminating browser {browser_id}")

    finally:
        await stagehand.close()
        logger.info("Terminated.")


async def inspect_command(id: str, option: Optional[str] = None):
    directory = f"data/profiles/{id}"

    # Use Stagehand with the existing profile directory
    stagehand = Stagehand(
        env="LOCAL",
        headless=False,
        local_browser_launch_options={"user_data_dir": directory, "headless": False},
    )
    await stagehand.init()

    try:
        page = stagehand.page
        if not page:
            raise RuntimeError("Stagehand page not available")

        if option and len(option) > 0:
            url = option if option.startswith("http") else f"https://{option}"
            await page.goto(url)

        # Keep the browser open for inspection
        # Note: In a real scenario, you might want to implement a way to keep it open
        await sleep(1)  # Brief pause before closing
    finally:
        await stagehand.close()


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
