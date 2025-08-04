import asyncio
import socket
from contextlib import asynccontextmanager
from datetime import datetime
from os import path
from typing import Final

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

from getgather.api.routes.auth.endpoints import router as auth_router
from getgather.api.routes.brands.endpoints import router as brands_router
from getgather.browser.profile import BrowserProfile
from getgather.browser.session import BrowserSession
from getgather.startup import startup
from getgather.mcp.main import mcp_app


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


STATIC_ASSETS_DIR = path.abspath(path.join(path.dirname(__file__), "..", "static", "assets"))
app.mount("/assets", StaticFiles(directory=STATIC_ASSETS_DIR), name="assets")


@app.get("/live")
def read_live():
    return PlainTextResponse(status_code=302, headers={"Location": "/live/index.html"})


NOVNC_DIR = path.abspath(path.join(path.dirname(__file__), "..", "3rdparty", "novnc"))
app.mount("/live", StaticFiles(directory=NOVNC_DIR), name="novnc")


@app.get("/", response_class=HTMLResponse)
def index():
    file_path = path.join(path.dirname(__file__), "frontend", "index.html")
    with open(file_path) as f:
        return HTMLResponse(content=f.read())


@app.websocket("/websockify")
async def vnc_websocket_proxy(websocket: WebSocket):
    """WebSocket proxy to bridge NoVNC client and VNC server."""
    await websocket.accept()

    try:
        vnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        vnc_socket.connect(("localhost", 5900))
        vnc_socket.setblocking(False)

        async def forward_to_vnc():
            try:
                while True:
                    data = await websocket.receive_bytes()
                    vnc_socket.send(data)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                print(f"Error forwarding to VNC: {e}")

        async def forward_from_vnc():
            try:
                while True:
                    await asyncio.sleep(0.001)
                    try:
                        data = vnc_socket.recv(4096)
                        if data:
                            await websocket.send_bytes(data)
                        else:
                            break  # Connection closed
                    except socket.error:
                        continue
            except Exception as e:
                print(f"Error forwarding from VNC: {e}")

        await asyncio.gather(forward_to_vnc(), forward_from_vnc(), return_exceptions=True)

    except ConnectionRefusedError:
        await websocket.send_text("Error: Could not connect to VNC server on port 5900")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        try:
            vnc_socket.close()
        except:
            pass
        try:
            await websocket.close()
        except:
            pass


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
app.mount("/mcp", mcp_app)
