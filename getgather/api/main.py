from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute

from getgather.api.routes.brands.endpoints import router as brands_router

from getgather.startup import startup

def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "no-tag"
    return f"{tag}-{route.name}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield

app = FastAPI(
    title="Get Gather API",
    description="API for Get Gather",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return PlainTextResponse(
        content=f"OK {int(datetime.now().timestamp())}"
    )

app.include_router(brands_router)