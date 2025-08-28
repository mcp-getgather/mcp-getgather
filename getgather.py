#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
import urllib.parse
from typing import TypedDict, cast

import nanoid
import pwinput
from bs4 import BeautifulSoup
from bs4.element import Tag
from patchright.async_api import BrowserContext, Page, async_playwright

from getgather.distill import Pattern, distill

NORMAL = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"
MAGENTA = "\033[35m"
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[36m"

ARROW = "⇢"
CROSS = "✘"

FRIENDLY_CHARS = "23456789abcdefghijkmnpqrstuvwxyz"


async def sleep(seconds: float):
    await asyncio.sleep(seconds)


async def ask(message: str, mask: str | None = None) -> str:
    if mask:
        return pwinput.pwinput(f"{message}: ", mask=mask)
    else:
        return input(f"{message}: ")


async def click(page: Page, selector: str, timeout: int = 3000) -> None:
    LOCATOR_ALL_TIMEOUT = 100
    locator = page.locator(selector)
    try:
        elements = await locator.all()
        print(f'Found {len(elements)} elements for selector "{selector}"')
        for element in elements:
            print("Checking", element)
            if await element.is_visible():
                print("Clicking on", element)
                try:
                    await element.click()
                    return
                except Exception as err:
                    print(f"Failed to click on {selector} {element}: {err}")
    except Exception as e:
        if timeout > 0 and "TimeoutError" in str(type(e)):
            print(f"retrying click {selector} {timeout}")
            await click(page, selector, timeout - LOCATOR_ALL_TIMEOUT)
            return
        raise e


def search(directory: str) -> list[str]:
    results: list[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            results.append(os.path.join(root, file))
    return results


def parse(html: str):
    return BeautifulSoup(html, "html.parser")


class Handle(TypedDict):
    id: str
    hostname: str
    location: str
    context: BrowserContext
    page: Page


async def init(location: str = "", hostname: str = "") -> Handle:
    global playwright_instance, browser_instance

    id = nanoid.generate(FRIENDLY_CHARS, 6)
    directory = f"data/profiles/{id}"

    if not playwright_instance:
        playwright_instance = await async_playwright().start()
        browser_instance = await playwright_instance.chromium.launch(
            headless=False, channel="chromium"
        )

    context = await playwright_instance.chromium.launch_persistent_context(  # type: ignore
        directory, headless=False, viewport={"width": 1920, "height": 1080}
    )

    page = context.pages[0] if context.pages else await context.new_page()
    return {"id": id, "hostname": hostname, "location": location, "context": context, "page": page}


def load_patterns() -> list[Pattern]:
    patterns: list[Pattern] = []
    for name in [f for f in search("./getgather/connectors/brand_specs") if f.endswith(".html")]:
        with open(name, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = parse(content)
        patterns.append({"name": name, "pattern": pattern})
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
        if element:
            selector = cast(Tag, element).get("gg-match")

        if element and selector:
            source = f"{domain}_{field}" if domain else field
            key = source.upper()
            value = os.getenv(key)

            if value and len(value) > 0:
                print(f"{CYAN}{ARROW} Using {BOLD}{key}{NORMAL} for {field}{NORMAL}")
                await page.fill(str(selector), value)
            else:
                placeholder = cast(Tag, element).get("placeholder")
                prompt = str(placeholder) if placeholder else f"Please enter {field}"
                mask = "*" if field == "password" else None
                await page.fill(str(selector), await ask(prompt, mask))
            await sleep(0.25)


async def autoclick(page: Page, distilled: str):
    document = parse(distilled)
    buttons = document.find_all(attrs={"gg-autoclick": True})

    for button in buttons:
        if isinstance(button, Tag):
            selector = button.get("gg-match")
            if selector:
                print(f"{CYAN}{ARROW} Auto-clicking {NORMAL}{selector}")
                await click(page, str(selector))


async def terminate(page: Page, distilled: str) -> bool:
    document = parse(distilled)
    stops = document.find_all(attrs={"gg-stop": True})
    if len(stops) > 0:
        print("Found stop elements, terminating session...")
        return True
    return False


playwright_instance = None
browser_instance = None


async def list_command():
    spec_files = search("./getgather/connectors/brand_specs")
    spec_files = [f for f in spec_files if f.endswith(".html")]

    for name in spec_files:
        print(name.replace("specs/", ""))


async def distill_command(location: str, option: str | None = None):
    patterns = load_patterns()

    print(f"Distilling {location}")

    async with async_playwright() as p:
        if location.startswith("http"):
            hostname = urllib.parse.urlparse(location).hostname
            browser = await p.chromium.launch(headless=False, channel="chromium")
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(location)
        else:
            hostname = option or ""
            browser = await p.chromium.launch(headless=False, channel="chromium")
            context = await browser.new_context()
            page = await context.new_page()

            with open(location, "r", encoding="utf-8") as f:
                content = f.read()
            await page.set_content(content)

        match = await distill(hostname, page, patterns)

        if match:
            distilled = match["distilled"]
            print()
            print(distilled)
            print()

        await browser.close()


async def run_command(location: str):
    if not location.startswith("http"):
        location = f"https://{location}"

    hostname = urllib.parse.urlparse(location).hostname or ""
    patterns = load_patterns()

    browser_data = await init(location, hostname)
    browser_id = browser_data["id"]
    context = browser_data["context"]
    page = browser_data["page"]

    print(f"Starting browser {browser_id}")

    print(f"{GREEN}{ARROW} Navigating to {NORMAL}{location}")
    await page.goto(location)

    TICK = 1  # seconds
    TIMEOUT = 15  # seconds
    max = TIMEOUT // TICK

    current = {"name": None, "distilled": None}

    try:
        for iteration in range(max):
            print()
            print(f"{MAGENTA}Iteration {iteration + 1}{NORMAL} of {max}")
            await sleep(TICK)

            match = await distill(hostname, page, patterns)
            if match:
                name = match["name"]
                distilled = match["distilled"]

                if distilled == current["distilled"]:
                    print(f"Still the same: {name}")
                else:
                    current = match
                    print()
                    print(distilled)
                    await autofill(page, distilled, ["email", "password", "tel", "text"])
                    await autoclick(page, distilled)

                    if await terminate(page, distilled):
                        break
            else:
                print(f"{CROSS}{RED} No matched pattern found{NORMAL}")

        print()
        print(f"Terminating browser {browser_id}")

    finally:
        await context.close()
        print("Terminated.")


async def inspect_command(id: str, option: str | None = None):
    directory = f"data/profiles/{id}"

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(directory, headless=False)
        page = context.pages[0] if context.pages else await context.new_page()

        if option and len(option) > 0:
            url = option if option.startswith("http") else f"https://{option}"
            await page.goto(url)

        await context.close()


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
        print("TODO: launch MCP server")
