# Get Gather

GetGather is a containerized service that allows MCP clients to interact with your data and act on your behalf.

## Quickstart

First, run the container with Docker or Podman:

```bash
docker run  -v /etc/localtime:/etc/localtime:ro -p 23456:23456 ghcr.io/mcp-getgather/mcp-getgather
```

On MacOS `-v /etc/localtime:/etc/localtime:ro` is needed for the service to use your local timezone,
and on Linux it's `-v /etc/timezone:/etc/timezone:ro` instead.
On windows, the timezone has to be set directly as `-e TZ=America/Los_Angeles`.

Optionally, with `--env-file` if you have an env file for OPENAI_API_KEY, etc.

```bash
docker run --env-file ~/getgather.env -p 23456:23456 ghcr.io/mcp-getgather/mcp-getgather
```

and then navigate to `http://localhost:23456/docs` to see the API docs.

To live stream the container desktop, go to `http://localhost:23456/live`.

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
      "url": "http://127.0.0.1:23456/mcp"
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
      "args": ["mcp-remote", "http://127.0.0.1:23456/mcp", "--allow-http"]
    }
  }
}
```

### (Optional) Enable url opener tool

Choose one of the following options if you'd like the MCP clients to automatically open the authentication link in a browser.

1. Add [playwright-mcp](https://github.com/microsoft/playwright-mcp/) server.
2. In Claude Desktop, enable "Control Chrome" in "Settings" -> "Extensions".

## MCP inspector

The container runs an [MCP inspector](https://github.com/modelcontextprotocol/inspector). It's useful for debugging and listing available tools without a client.

Run docker container with additional port 6277

```bash
docker run -p 23456:23456 -p 6277:6277 ghcr.io/mcp-getgather/mcp-getgather
```

Open [inspector url](http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=getgather&transport=streamable-http&serverUrl=http://localhost:23456/mcp) in your browser.

The default `MCP_PROXY_AUTH_TOKEN` is `getgather`. You can change it by running the container with `--env MCP_PROXY_AUTH_TOKEN=SOME_TOKEN`.

The inspector can be disabled with `--env MCP_INSPECTOR_DISABLED=true`.

## Build and run locally

After cloning the repo:

```bash
docker build -t mcp-getgather .
docker run -p 23456:23456 mcp-getgather
```

### Proxy Configuration

Get Gather supports using an external proxy service for browser sessions. To enable proxy support, set the following environment variables:

```bash
BROWSER_HTTP_PROXY=http://your-proxy-server:port
BROWSER_HTTP_PROXY_PASSWORD=your-proxy-password
```

The proxy service should use hierarchical location-based routing if location information is provided. The username format sent to the proxy server will be:

- Basic: `profile_id`
- With location: `profile_id-city_X_state_Y_country_Z`

### Repo file structure

[Diagram](./diagram.md) (generated at [GitDiagram](https://gitdiagram.com/getgather-hub/getgather))
