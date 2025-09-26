"""Tests for NYTimes Tools: get_bestsellers_list."""

import json
import os

import pytest
from fastmcp import Client
from mcp.types import TextContent

config = {
    "mcpServers": {"getgather": {"url": f"{os.environ.get('HOST', 'http://localhost:23456')}/mcp"}}
}


@pytest.mark.mcp
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Flaky test")
async def test_nytimes_get_bestsellers_list():
    """Test get bestsellers list from NY Times."""
    client = Client(config)
    async with client:
        mcp_call_result = await client.call_tool("nytimes_get_bestsellers_list")
        assert isinstance(mcp_call_result.content[0], TextContent), (
            f"Expected TextContent, got {type(mcp_call_result.content[0])}"
        )
        parsed_mcp_call_result = json.loads(mcp_call_result.content[0].text)
        best_sellers = parsed_mcp_call_result.get("best_sellers")
        assert best_sellers, "Expected 'best_sellers' to be non-empty"
        assert isinstance(best_sellers, list), f"Expected list, got {type(best_sellers)}"
