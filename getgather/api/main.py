from contextlib import asynccontextmanager
from datetime import datetime
from os import path
from typing import Final

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

from getgather.api.routes.auth.endpoints import router as auth_router
from getgather.api.routes.brands.endpoints import router as brands_router
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
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


STATIC_ASSETS_DIR = path.abspath(path.join(path.dirname(__file__), "..", "static", "assets"))
app.mount("/assets", StaticFiles(directory=STATIC_ASSETS_DIR), name="assets")


@app.get("/", response_class=HTMLResponse)
def index():
    file_path = path.join(path.dirname(__file__), "frontend", "index.html")
    with open(file_path) as f:
        return HTMLResponse(content=f.read())


@app.get("/start/{brand}", response_class=HTMLResponse)
def start(brand: str):
    file_path = path.join(path.dirname(__file__), "frontend", "start.html")
    with open(file_path) as f:
        template = Template(f.read())
    rendered = template.render(brand=brand)
    return HTMLResponse(content=rendered)


@app.get("/health")
def health():
    return PlainTextResponse(content=f"OK {int(datetime.now().timestamp())}")


IP_CHECK_URL: Final[str] = "https://ifconfig.me/ip"


@app.get("/extended-health")
async def extended_health():
    browser_profile = BrowserProfile.create()
    session = await BrowserSession.get(browser_profile)
    try:
        await session.start()
        page = await session.page()
        await page.goto(IP_CHECK_URL, timeout=3000)
        ip_text: str = await page.evaluate("() => document.body.innerText.trim()")
    except Exception as e:
        return PlainTextResponse(content=f"Error: {e}")
    finally:
        await session.stop()
    return PlainTextResponse(content=f"OK IP: {ip_text}")


app.include_router(brands_router)
app.include_router(auth_router)
