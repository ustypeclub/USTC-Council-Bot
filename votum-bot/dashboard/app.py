"""FastAPI application for the Votum dashboard.

The dashboard provides a read/write interface for councils, motions and
archives.  It authenticates users via Discord OAuth2 and uses Jinja2
templates for HTML rendering.  Live vote tallies are delivered over a
WebSocket endpoint.
"""

from __future__ import annotations

import os
import logging

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import get_current_user, login as login_route, callback as callback_route

# Import API routers
from .routers import councils, motions, votes, archives, configs as configs_router

log = logging.getLogger(__name__)

app = FastAPI()

# Mount static files and templates
BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Include API routers
app.include_router(councils.router)
app.include_router(motions.router)
app.include_router(votes.router)
app.include_router(archives.router)
app.include_router(configs_router.router)


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, user: dict = Depends(get_current_user)):
    """Render the dashboard home page.

    For demonstration this page simply lists that the user is logged in.  A
    complete implementation would query the bot database for councils and
    motions and display statistics.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/login")
async def login(request: Request):
    """Redirect to Discord for login."""
    return await login_route(request)


@app.get("/api/auth/callback")
async def auth_callback(request: Request):
    """Discord OAuth2 callback."""
    return await callback_route(request)


@app.websocket("/ws/tally")
async def websocket_tally(websocket: WebSocket):
    """WebSocket endpoint to send live vote tallies to clients.

    For this example the endpoint simply echoes back received messages.  A full
    implementation would subscribe to an internal event bus that broadcasts
    vote totals whenever they change.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        pass