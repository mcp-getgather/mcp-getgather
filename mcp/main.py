from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient
from typing import Any
import webbrowser
import os

getgather_mcp_proxy = FastMCP.as_proxy(
    ProxyClient[Any](os.getenv("GETGATHER_MCP_URL", "http://127.0.0.1:8000/mcp")),
    name="GetGather MCP Proxy",
)


@getgather_mcp_proxy.tool
async def open_url(
    url: str,
) -> dict[str, Any]:
    """Open a url in the browser."""
    webbrowser.open(url)
    return {
        "success": True,
    }


if __name__ == "__main__":
    getgather_mcp_proxy.run()
