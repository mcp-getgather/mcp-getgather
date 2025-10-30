#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
import urllib.parse
from glob import glob

from getgather.browser.profile import BrowserProfile
from getgather.browser.session import browser_session
from getgather.config import settings
from getgather.distill import (
    distill,
    load_distillation_patterns,
    run_distillation_loop,
)
from getgather.logs import logger

_ = settings.LOG_LEVEL


PATTERNS_LOCATION = "./getgather/mcp/patterns/**/*.html"


async def list_command():
    spec_files = glob(PATTERNS_LOCATION, recursive=True)
    spec_files = [f for f in spec_files if f.endswith(".html")]

    for name in spec_files:
        logger.info(os.path.basename(name))


async def distill_command(location: str, option: str | None = None):
    patterns = load_distillation_patterns(PATTERNS_LOCATION)

    logger.info(f"Distilling {location} using {len(patterns)} patterns")

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
    patterns = load_distillation_patterns(PATTERNS_LOCATION)

    if not location.startswith("http"):
        location = f"https://{location}"

    _terminated, distilled, converted = await run_distillation_loop(location, patterns=patterns)
    result = converted if converted else distilled
    print(result)

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

        input("Press Enter to terminate session...")


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
