#!/usr/bin/env python3
"""Extract OpenAPI schema from FastAPI app without running the server."""
from getgather.api.api import api_app
openapi_schema = api_app.openapi()
