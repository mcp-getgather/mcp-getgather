import asyncio
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute

from getgather.api.routes.activities.endpoints import router as activities_router
from getgather.api.routes.auth.endpoints import router as auth_router
from getgather.api.routes.brands.endpoints import router as brands_router
from getgather.api.routes.link.endpoints import router as link_router
from getgather.config import settings
from getgather.mcp.main import MCPDoc, create_mcp_apps, mcp_app_docs


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "no-tag"
    return f"{tag}-{route.name}"


api_app = FastAPI(
    title="Get Gather API",
    description="API for Get Gather",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    generate_unique_id_function=custom_generate_unique_id,
)

api_app.include_router(activities_router)
api_app.include_router(brands_router)
api_app.include_router(auth_router)
api_app.include_router(link_router)


@api_app.get("/health")
def health():
    return PlainTextResponse(
        content=f"API OK {int(datetime.now().timestamp())} GIT_REV: {settings.GIT_REV}"
    )


@api_app.get("/mcp-docs")
async def mcp_docs() -> list[MCPDoc]:
    return await asyncio.gather(*[mcp_app_docs(mcp_app) for mcp_app in create_mcp_apps()])
