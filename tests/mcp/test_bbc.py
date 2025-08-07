"""Tests for BBC Tools: login, get_bookmarks."""

import json
import os

import pytest
from fastmcp import Client
from mcp.types import TextContent
from playwright.async_api import async_playwright

config = {"mcpServers": {"getgather": {"url": f"{os.environ.get('HOST')}/mcp"}}}


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_bbc_login_and_get_bookmarks():
    """Test login to bbc."""
    async with async_playwright() as p:
        client = Client(config)
        async with client:
            mcp_call_auth = await client.call_tool("bbc_get_bookmarks")
            assert isinstance(mcp_call_auth.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_auth.content[0])}"
            )
            mcp_call_auth_result = json.loads(mcp_call_auth.content[0].text)
            assert mcp_call_auth_result.get("url")
            assert mcp_call_auth_result.get("session_id")
            print(mcp_call_auth_result.get("url"))

            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url=mcp_call_auth_result.get("url"), wait_until="domcontentloaded")

            await page.wait_for_selector("input[data-testid='input-email']")
            await page.type("input[data-testid='input-email']", os.environ.get("BBC_EMAIL", ""))
            await page.click("button[type='submit']")

            await page.wait_for_selector("input[data-testid='input-password']")
            await page.type(
                "input[data-testid='input-password']", os.environ.get("BBC_PASSWORD", "")
            )
            await page.click("button[type='submit']")

            await page.wait_for_selector(
                "p:has-text('Authentication successful! You can go back to the app now.')"
            )

            mcp_call_poll_auth = await client.call_tool(
                "poll_auth", {"session_id": mcp_call_auth_result.get("session_id")}
            )
            assert isinstance(mcp_call_poll_auth.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_poll_auth.content[0])}"
            )
            mcp_call_poll_auth_result = json.loads(mcp_call_poll_auth.content[0].text)
            assert mcp_call_poll_auth_result.get("status") == "FINISHED"

            mcp_call_get_bookmarks = await client.call_tool("bbc_get_bookmarks")
            assert isinstance(mcp_call_get_bookmarks.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_get_bookmarks.content[0])}"
            )
            mcp_call_get_bookmarks_result = json.loads(mcp_call_get_bookmarks.content[0].text)
            assert isinstance(mcp_call_get_bookmarks_result["extract_result"], list), (
                "extract_result should be a list"
            )
            assert len(mcp_call_get_bookmarks_result["extract_result"]) > 0, (
                "extract_result should not be empty"
            )
