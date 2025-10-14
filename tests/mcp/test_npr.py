"""Tests for NPR Tools: get_headlines."""

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
async def test_npr_get_headlines():
    """Test get headlines from NPR."""
    client = Client(config)
    async with client:
        mcp_call_result = await client.call_tool("npr_get_headlines")
        assert isinstance(mcp_call_result.content[0], TextContent), (
            f"Expected TextContent, got {type(mcp_call_result.content[0])}"
        )
        parsed_mcp_call_result = json.loads(mcp_call_result.content[0].text)
        headlines = parsed_mcp_call_result.get("headlines")
        assert headlines, "Expected 'headlines' to be non-empty"
        assert isinstance(headlines, list), f"Expected list, got {type(headlines)}"
