import json

import httpx
import pytest
from fastmcp import Client
from mcp.types import TextContent
from playwright.async_api import async_playwright

config = {"mcpServers": {"getgather": {"url": f"http://127.0.0.1:8000/mcp"}}}


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_goodreads_login_and_get_books():
    """Test login to bbc."""
    async with async_playwright() as p:
        client = Client(config)
        async with client:
            mcp_call_auth = await client.call_tool("goodreads_get_book_list")
            assert isinstance(mcp_call_auth.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_auth.content[0])}"
            )
            mcp_call_auth_result = json.loads(mcp_call_auth.content[0].text)
            assert mcp_call_auth_result.get("url")
            assert mcp_call_auth_result.get("link_id")
            print(mcp_call_auth_result.get("url"))

            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url=mcp_call_auth_result.get("url"), wait_until="domcontentloaded")

            await page.wait_for_selector("input[data-testid='input-email']")
            await page.type("input[data-testid='input-email']", "faisalburhanudin@gmail.com")
            await page.click("button[type='submit']")

            await page.wait_for_selector("input[data-testid='input-password']")
            await page.type(
                "input[data-testid='input-password']", "xWmRoZF1dh4OB9"
            )
            await page.click("button[type='submit']")

            await page.wait_for_selector(
                "p:has-text('Authentication successful! You can go back to the app now.')"
            )

            mcp_call_poll_auth = await client.call_tool(
                "poll_auth", {"link_id": mcp_call_auth_result.get("link_id")}
            )
            assert isinstance(mcp_call_poll_auth.content[0], TextContent), (
                f"Expected TextContent, got {type(mcp_call_poll_auth.content[0])}"
            )
            mcp_call_poll_auth_result = json.loads(mcp_call_poll_auth.content[0].text)
            assert mcp_call_poll_auth_result.get("status") == "FINISHED"


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_activities_endpoint():
    """Test /api/activities endpoint to ensure activities are created."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8000/api/activities/")
        assert response.status_code == 200
        
        activities = response.json()
        print(f"Activities response: {activities}")
        assert isinstance(activities, list), "Activities endpoint should return a list"
        assert len(activities) > 0, "Activities list should not be empty"
        
        # Verify the structure of the first activity
        activity = activities[0]
        print(f"First activity: {activity}")
        assert "id" in activity, "Activity should have an id field"
        assert "brand_id" in activity, "Activity should have a brand_id field"
        assert "name" in activity, "Activity should have a name field"
        assert "start_time" in activity, "Activity should have a start_time field"


@pytest.mark.mcp
@pytest.mark.asyncio
async def test_recordings_endpoint():
    """Test /api/activities/{activity_id}/recordings endpoint to ensure rrweb recordings are created."""
    async with httpx.AsyncClient() as client:
        # First get activities to find one with a recording
        activities_response = await client.get("http://127.0.0.1:8000/api/activities/")
        assert activities_response.status_code == 200
        
        activities = activities_response.json()
        print(f"Activities for recordings test: {activities}")
        
        # Find an activity that has a recording
        activity_with_recording = None
        for activity in activities:
            print(f"Activity: {activity.get('id')}, has_recording: {activity.get('has_recording')}")
            if activity.get("has_recording"):
                activity_with_recording = activity
                break
        
        assert activity_with_recording is not None, "At least one activity should have a recording"
        activity_id = activity_with_recording["id"]
        print(f"Testing recordings for activity: {activity_id}")
        
        # Test the recordings endpoint
        recording_response = await client.get(f"http://127.0.0.1:8000/api/activities/{activity_id}/recordings")
        assert recording_response.status_code == 200
        
        recording = recording_response.json()
        print(f"Recording response: {recording}")
        assert "activity_id" in recording, "Recording should have activity_id field"
        assert "events" in recording, "Recording should have events field"
        assert recording["activity_id"] == activity_id, "Recording activity_id should match requested activity"
        assert isinstance(recording["events"], list), "Recording events should be a list"
        assert len(recording["events"]) > 0, "Recording events should not be empty"
