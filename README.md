# Get Gather

First, run the container with Docker or Podman:

```bash
docker run -p 8000:8000 ghcr.io/mcp-getgather/mcp-getgather
```

and then navigate to `http://localhost:8000/docs` to see the API docs.

To live stream the container desktop, go to `http://localhost:8000/live`.

All additional documentation is located in the [docs](./docs) directory:

- [Deploying on Dokku](./docs/deploy_dokku.md)
- [Deploying on Fly.io](./docs/deploy_fly.md)
- [Deploying on Railway](./docs/deploy_railway.md)

## MCP configuration

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

```bash
docker build -t mcp-getgather .
docker run -p 8000:8000 mcp-getgather
```

## Repo file structure

[Diagram](./diagram.md) (generated at [GitDiagram](https://gitdiagram.com/getgather-hub/getgather))
