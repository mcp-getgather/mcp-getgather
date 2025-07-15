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

- [Deploying on Fly.io](./docs/deploy_fly.md)
- [Deploying on Railway](./docs/deploy_railway.md)
