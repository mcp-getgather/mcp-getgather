import asyncio
import os
import secrets
import socket
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from os import path
from typing import Final
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

from getgather.api.routes.auth.endpoints import router as auth_router
from getgather.api.routes.brands.endpoints import router as brands_router
from getgather.api.routes.link.endpoints import router as link_router
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.config import settings
from getgather.hosted_link_manager import HostedLinkManager
from getgather.logs import logger
from getgather.mcp.main import mcp_app
from getgather.startup import startup


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "no-tag"
    return f"{tag}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    async with mcp_app.lifespan(app):  # type: ignore
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



_inspector_proc: subprocess.Popen[str] | None = None
_inspector_token: str | None = None

STATIC_ASSETS_DIR = path.abspath(path.join(path.dirname(__file__), "..", "static", "assets"))
BUILD_ASSETS_DIR = path.abspath(path.join(path.dirname(__file__), "frontend", "assets"))

app.mount("/static/assets", StaticFiles(directory=STATIC_ASSETS_DIR), name="assets")
app.mount("/assets", StaticFiles(directory=BUILD_ASSETS_DIR), name="assets")


@app.get("/live")
def read_live():
    return RedirectResponse(url="/live/", status_code=301)


@app.get("/live/{file_path:path}")
async def proxy_live_files(file_path: str):
    # noVNC lite's main web UI
    if file_path == "" or file_path == "old-index.html":
        local_file_path = path.join(path.dirname(__file__), "frontend", "live.html")
        with open(local_file_path) as f:
            return HTMLResponse(content=f.read())

    # Proxy noVNC libraries to unpkg.com
    unpkg_url = f"https://unpkg.com/@novnc/novnc@1.3.0/{file_path}"

    logger.info(f"Proxying {file_path} to {unpkg_url}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(unpkg_url)
            content = response.content
            logger.debug(f"Response's length: {len(content)}")

            # Filter out headers that can cause decoding issues
            headers = dict(response.headers)
            for header in ["content-encoding", "content-length", "transfer-encoding"]:
                headers.pop(header, None)

            return Response(status_code=response.status_code, content=content, headers=headers)
        except httpx.RequestError:
            return Response(status_code=404)


@app.get("/", response_class=HTMLResponse)
def index():
    file_path = path.join(path.dirname(__file__), "frontend", "old-index.html")
    with open(file_path) as f:
        return HTMLResponse(content=f.read())


@app.websocket("/websockify")
async def vnc_websocket_proxy(websocket: WebSocket):
    """WebSocket proxy to bridge NoVNC client and VNC server."""
    await websocket.accept()

    vnc_socket = None
    websocket_closed = asyncio.Event()

    try:
        vnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        vnc_socket.connect(("localhost", 5900))
        vnc_socket.setblocking(False)

        async def forward_to_vnc():
            try:
                while not websocket_closed.is_set():
                    data = await websocket.receive_bytes()
                    vnc_socket.send(data)
            except WebSocketDisconnect:
                websocket_closed.set()
            except Exception as e:
                logger.error(f"Error forwarding to VNC: {e}")
                websocket_closed.set()

        async def forward_from_vnc():
            try:
                while not websocket_closed.is_set():
                    await asyncio.sleep(0.001)
                    try:
                        data = vnc_socket.recv(4096)
                        if data:
                            if not websocket_closed.is_set():
                                await websocket.send_bytes(data)
                        else:
                            break  # VNC connection closed
                    except socket.error:
                        continue
            except Exception as e:
                logger.error(f"Error forwarding from VNC: {e}")
            finally:
                websocket_closed.set()

        await asyncio.gather(forward_to_vnc(), forward_from_vnc(), return_exceptions=True)

    except ConnectionRefusedError:
        if not websocket_closed.is_set():
            try:
                await websocket.send_text("Error: Could not connect to VNC server on port 5900")
            except:
                pass
    except Exception as e:
        if not websocket_closed.is_set():
            try:
                await websocket.send_text(f"Error: {str(e)}")
            except:
                pass
    finally:
        websocket_closed.set()
        try:
            if vnc_socket is not None:
                vnc_socket.close()
        except:
            pass
        try:
            if websocket.client_state.value <= 2:  # CONNECTING or CONNECTED
                await websocket.close()
        except:
            pass

def _ensure_inspector_running() -> str:
    global _inspector_proc, _inspector_token
    if _inspector_proc is not None and _inspector_proc.poll() is None and _inspector_token is not None:
        return _inspector_token

    token = secrets.token_hex(32)
    env = os.environ.copy()
    env["MCP_AUTO_OPEN_ENABLED"] = "false"
    env["MCP_PROXY_AUTH_TOKEN"] = token
    env.setdefault("HOST", "127.0.0.1")

    _inspector_proc = subprocess.Popen(
        ["npx", "@modelcontextprotocol/inspector"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    _inspector_token = token
    return token


@app.get("/inspector")
def inspector(request: Request):
    token = _ensure_inspector_running()
    base = str(request.base_url).rstrip("/")
    server_url = f"{base}/mcp"
    target = (
        "http://localhost:6274/"
        f"?MCP_PROXY_AUTH_TOKEN={token}"
        f"&transport=streamable-http&serverUrl={quote(server_url, safe=':/')}"
    )
    return RedirectResponse(url=target, status_code=307)

@app.get("/start/{brand}", response_class=HTMLResponse)
def start(brand: str):
    file_path = path.join(path.dirname(__file__), "frontend", "start.html")
    with open(file_path) as f:
        template = Template(f.read())
    rendered = template.render(brand=brand)
    return HTMLResponse(content=rendered)


@app.get("/activities")
def activities():
    file_path = path.join(path.dirname(__file__), "frontend", "index.html")
    with open(file_path) as f:
        template = Template(f.read())
    rendered = template.render()
    return HTMLResponse(content=rendered)


@app.get("/health")
def health():
    return PlainTextResponse(
        content=f"OK {int(datetime.now().timestamp())} GIT_REV: {settings.GIT_REV}"
    )


@app.get("/link/{link_id}", response_class=HTMLResponse)
async def link_page(link_id: str):
    """Serve the hosted link frontend page for user authentication."""

    # Look up the brand from the link store
    link_data = HostedLinkManager.get_link_data(link_id)
    if not link_data:
        raise HTTPException(status_code=404, detail=f"Link ID '{link_id}' not found")

    brand = str(link_data.brand_id)
    redirect_url = link_data.redirect_url

    file_path = path.join(path.dirname(__file__), "frontend", "link.html")
    with open(file_path) as f:
        template = Template(f.read())
    rendered = template.render(brand=brand, link_id=link_id, redirect_url=redirect_url)
    return HTMLResponse(content=rendered)


IP_CHECK_URL: Final[str] = "https://ifconfig.me/ip"


@app.get("/extended-health")
async def extended_health():
    session = await BrowserSession.get(BrowserProfile())
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
app.include_router(link_router)
app.mount("/mcp", mcp_app)
