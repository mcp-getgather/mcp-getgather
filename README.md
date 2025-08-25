# Get Gather

GetGather is a containerized service that allows MCP clients to interact with your data and act on your behalf.

## Quickstart

Download the [docker-compose.yml](https://github.com/mcp-getgather/mcp-getgather/blob/main/docker-compose.yml) file and run

```bash
docker-compose up -d
```

(You will need to install [Docker](https://www.docker.com/products/docker-desktop/) first)

and then navigate to `http://localhost:23456/welcome` to see the docs.

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

## Build and run locally

After cloning the repo:

```bash
docker build -t mcp-getgather .
docker run -p 23456:23456 -p 6277:6277 mcp-getgather
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

## Deployment

Check out documentations located in the [docs](./docs) directory:

- [Local Development Setup](./docs/local-development.md)
- [Deploying on Dokku](./docs/deploy_dokku.md)
- [Deploying on Fly.io](./docs/deploy_fly.md)
- [Deploying on Railway](./docs/deploy_railway.md)
