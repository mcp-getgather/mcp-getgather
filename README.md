# Get Gather

## Repo file structure
[Diagram](./diagram.md) (genereated at [GitDiagram](https://gitdiagram.com/getgather-hub/getgather))

## Build and run locally

```bash
docker build -t getgather .
docker run -p 8000:8000 --name getgather -d getgather
```

and then navigate to `http://localhost:8000/docs` to see the API docs.

All additional documentation is located in the [docs](./docs) directory:

- [Deploying on Dokku](./docs/deploy_dokku.md)
- [Deploying on Fly.io](./docs/deploy_fly.md)
- [Deploying on Railway](./docs/deploy_railway.md)


## MCP configuration

```json
{
  "mcpServers": {
    "getgather": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "GOODREADS_EMAIL": "example@gmail.com",
        "GOODREADS_PASSWORD": "examplepassword",
      }
    }
  }
}
```