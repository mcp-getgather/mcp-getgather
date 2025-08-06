# GetGather Local MCP Quick Start

## Option 1: Using docker image

1. Download the docker image from registry (link to be added) or build from
   source code by following the instructions below.

2. Download [mcp-getgather.sh](https://github.com/gather-engineering/dax/blob/main/getgather/mcp/mcp-getgather.py). Remember the path to the file to be used in the next step.

3. Start docker container

```bash
docker run -d -p 8000:8000 -e HOST_URL_OPENER=/host_url_opener -v ~/.cache/getgather:/host_url_opener getgather
```

4. Add the json blob below to the .json configuration file of your mcp client, then restart your client.
   For example, if you MacOS Claude Desktop, the file is `~/Library/Application Support/Claude/claude_desktop_config.json`.

```json
{
  "mcpServers": {
    "getgather": {
      "command": "bash",
      "args": ["/path/to/mcp-getgather.sh"]
    }
  }
}
```

## Option 2: Using source code

1. Building the Docker Image

```bash
docker build -t getgather .
```

2. Running the Container

```bash
docker run -d -p 8000:8000 getgather
```

3. MCP configuration

```json
{
  "mcpServers": {
    "getgather": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-getgather", "run", "mcp/main.py"],
      "env": {
        "GETGATHER_MCP_URL": "http://127.0.0.1:8000/mcp"
      }
    }
  }
}
```
