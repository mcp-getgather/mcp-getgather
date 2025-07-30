# Get Gather

## Repo file structure
[Diagram](./diagram.md) (genereated at [GitDiagram](https://gitdiagram.com/getgather-hub/getgather))

## Build and run locally

```bash
docker build -t getgather .
docker run -p 8000:8000 --name getgather -d getgather
```
and then navigate to `http://localhost:8000/docs` to see the API docs.

Optionally, if you want to live stream the container desktop, run docker with additional parameters
```bash
-e VNC_PASSWORD=$YOUR_VNC_PASSWORD -p 5900:5900
```

All additional documentation is located in the [docs](./docs) directory:

- [Deploying on Dokku](./docs/deploy_dokku.md)
- [Deploying on Fly.io](./docs/deploy_fly.md)
- [Deploying on Railway](./docs/deploy_railway.md)


## MCP configuration

```json
{
  "mcpServers": {
    "getgather": {
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "GOODREADS_EMAIL": "example@gmail.com",
        "GOODREADS_PASSWORD": "examplepassword",
      }
    }
  }
}
```


For Claude Desktop (also works for Cursor)

```json
{
  "mcpServers": {
    "getgather": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:8000/mcp",
        "--header",
        "GOODREADS_EMAIL: ${GOODREADS_EMAIL}",
        "--header",
        "GOODREADS_PASSWORD: ${GOODREADS_PASSWORD}"
      ],
      "env": {
        "GOODREADS_EMAIL": "example@email.com",
        "GOODREADS_PASSWORD": "examplepassword"
      }
    }
  }
}
```

## Live stream container desktop 

On MacOS
- Open `Finder -> Go -> Connect to Server...`
- Enter Server Address `vnc://localhost:5900`
- Enter password `$YOUR_VNC_PASSWORD`, which is set at `docker run`

You can use other VNC clients in a similar way.