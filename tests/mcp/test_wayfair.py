"""Tests for Wayfair Tools: login, get_order_history"""

import json
import os

import pytest
from dotenv import load_dotenv
from fastmcp import Client
from mcp.types import TextContent
from patchright.async_api import async_playwright

load_dotenv()

config = {
    "mcpServers": {"getgather": {"url": f"{os.environ.get('HOST', 'http://localhost:23456')}/mcp"}}
}


@pytest.mark.mcp
@pytest.mark.asyncio
@pytest.mark.xfail(reason="flaky")
async def test_wayfair_login_and_get_order_history():
    """Test login to wayfair and get order history."""
    async with async_playwright() as p:
        client = Client(config)
        async with client:
            mcp_call_tool = await client.call_tool("wayfair_get_order_history")
            assert isinstance(mcp_call_tool.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_tool.content[0])}"
            )
            mcp_call_signin_result = json.loads(mcp_call_tool.content[0].text)
            assert mcp_call_signin_result.get("url")
            assert mcp_call_signin_result.get("signin_id")
            print(mcp_call_signin_result.get("url"))

            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url=mcp_call_signin_result.get("url"), wait_until="domcontentloaded")

            await page.wait_for_selector("input[type=email]")
            await page.type("input[type=email]", os.environ.get("WAYFAIR_EMAIL", ""))
            await page.click("button[type='submit']")

            await page.wait_for_selector(":has-text('Sign In With Your Password')")
            await page.click("button:has-text('Sign In With Your Password')")

            await page.wait_for_selector("input[type=password]")
            await page.type("input[type=password]", os.environ.get("WAYFAIR_PASSWORD", ""))
            await page.click("button[type='submit']")

            await page.wait_for_selector(":has-text('Finished! You can close this window now.')")

            mcp_call_check_signin = await client.call_tool(
                "check_signin", {"signin_id": mcp_call_signin_result.get("signin_id")}
            )
            assert isinstance(mcp_call_check_signin.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_check_signin.content[0])}"
            )
            mcp_call_check_signin_result = json.loads(mcp_call_check_signin.content[0].text)
            assert mcp_call_check_signin_result.get("status") == "SUCCESS"

            mcp_call_get_order_history = await client.call_tool("wayfair_get_order_history")
            assert isinstance(mcp_call_get_order_history.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_get_order_history.content[0])}"
            )
            parsed_mcp_call_result = json.loads(mcp_call_get_order_history.content[0].text)
            order_history = parsed_mcp_call_result.get("wayfair_order_history")
            print(order_history)
            assert order_history, "Expected 'order_history' to be non-empty"
            assert isinstance(order_history, list), f"Expected list, got {type(order_history)}"


@pytest.mark.mcp
@pytest.mark.asyncio
@pytest.mark.xfail(reason="flaky")
async def test_wayfair_get_cart():
    """Test get cart from wayfair."""
    client = Client(config)
    async with client:
        mcp_call_get_cart = await client.call_tool("wayfair_get_cart")
        assert isinstance(mcp_call_get_cart.content[0], TextContent), (
            f"Expected TextContent, got {type(mcp_call_get_cart.content[0])}"
        )
        parsed_mcp_call_result = json.loads(mcp_call_get_cart.content[0].text)
        cart = parsed_mcp_call_result.get("wayfair_cart")
        print(cart)
        assert cart, "Expected 'cart' to be non-empty"
        assert isinstance(cart, list), f"Expected list, got {type(cart)}"


@pytest.mark.mcp
@pytest.mark.asyncio
@pytest.mark.xfail(reason="flaky")
async def test_wayfair_get_wishlists():
    """Test get wishlists from wayfair."""
    client = Client(config)
    async with client:
        mcp_call_get_wishlists = await client.call_tool("wayfair_get_wishlists")
        assert isinstance(mcp_call_get_wishlists.content[0], TextContent), (
            f"Expected TextContent, got {type(mcp_call_get_wishlists.content[0])}"
        )
        parsed_mcp_call_result = json.loads(mcp_call_get_wishlists.content[0].text)
        wishlists = parsed_mcp_call_result.get("wayfair_wishlists")
        print(wishlists)
        assert wishlists, "Expected 'wishlists' to be non-empty"
        assert isinstance(wishlists, list), f"Expected list, got {type(wishlists)}"
