# Get Gather
GetGather is a containerized service that allows MCP clients to interact with your data and act on your behalf.

## Quickstart
First, run the container with Docker or Podman:

```bash
docker run -p 8000:8000 ghcr.io/mcp-getgather/mcp-getgather
```

and then navigate to `http://localhost:8000/docs` to see the API docs.

To live stream the container desktop, go to `http://localhost:8000/live`.

All additional documentation is located in the [docs](./docs) directory:

- [Local Development Setup](./docs/local-development.md)
- [Deploying on Dokku](./docs/deploy_dokku.md)
- [Deploying on Fly.io](./docs/deploy_fly.md)
- [Deploying on Railway](./docs/deploy_railway.md)

### MCP configuration

For VS Code, Cursor, and other MCP clients which support remote MCP servers:

```json
{
  "mcpServers": {
    "getgather": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

For Claude Desktop:

```json
{
  "mcpServers": {
    "getgather": {
      "command": "npx",
      "args": ["mcp-remote", "http://127.0.0.1:8000/mcp", "--allow-http"]
    }
  }
}
```

### (Optional) Enable url opener tool

Choose one of the following options if you'd like the MCP clients to automatically open the authentication link in a browser.

1. Add [playwright-mcp](https://github.com/microsoft/playwright-mcp/) server.
2. In Claude Desktop, enable "Control Chrome" in "Settings" -> "Extensions".

## Build and run locally
After cloning the repo:

```bash
docker build -t mcp-getgather .
docker run -p 8000:8000 mcp-getgather
```

### Proxy Configuration

Get Gather supports using an external proxy service for browser sessions. To enable proxy support, set the following environment variables:

```bash
HTTP_PROXY=http://your-proxy-server:port
HTTP_PROXY_PASSWORD=your-proxy-password
```

The proxy service should use hierarchical location-based routing if location information is provided. The username format sent to the proxy server will be:

- Basic: `profile_id`
- With location: `profile_id-city_X_state_Y_country_Z`

### Repo file structure

[Diagram](./diagram.md) (generated at [GitDiagram](https://gitdiagram.com/getgather-hub/getgather))
