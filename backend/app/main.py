import logging
from contextlib import asynccontextmanager
import os
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.socket.server import sio
import app.socket.agent_namespace  # noqa: F401 — registers handlers
import app.socket.widget_namespace  # noqa: F401 — registers handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    from app.background.scheduler import start_scheduler

    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down...")
    from app.background.scheduler import stop_scheduler

    stop_scheduler()


fastapi_app = FastAPI(
    title="Intercom Clone API",
    version="1.0.0",
    description="Production-ready customer communication platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, settings.WIDGET_CDN_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
from app.routers import (
    auth,
    team,
    conversations,
    contacts,
    inboxes,
    kb,
    canned_responses,
    ai,
    email_inbound,
    domains,
    sla,
    webhooks,
    api_keys,
    analytics,
    widget,
    public_kb,
)

fastapi_app.include_router(auth.router, prefix="/api/v1")
fastapi_app.include_router(team.router, prefix="/api/v1")
fastapi_app.include_router(conversations.router, prefix="/api/v1")
fastapi_app.include_router(contacts.router, prefix="/api/v1")
fastapi_app.include_router(inboxes.router, prefix="/api/v1")
fastapi_app.include_router(kb.router, prefix="/api/v1")
fastapi_app.include_router(canned_responses.router, prefix="/api/v1")
fastapi_app.include_router(ai.router, prefix="/api/v1")
fastapi_app.include_router(email_inbound.router, prefix="/api/v1")
fastapi_app.include_router(domains.router, prefix="/api/v1")
fastapi_app.include_router(sla.router, prefix="/api/v1")
fastapi_app.include_router(webhooks.router, prefix="/api/v1")
fastapi_app.include_router(api_keys.router, prefix="/api/v1")
fastapi_app.include_router(analytics.router, prefix="/api/v1")
fastapi_app.include_router(widget.router, prefix="/api/v1")
fastapi_app.include_router(public_kb.router, prefix="/api/v1")


@fastapi_app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


# Serve widget bundle if it exists
widget_dist = os.path.join(os.path.dirname(__file__), "..", "widget", "dist")
if os.path.exists(widget_dist):
    fastapi_app.mount("/widget", StaticFiles(directory=widget_dist), name="widget")

# Mount socket.io ASGI app
app = socketio.ASGIApp(
    sio,
    other_asgi_app=fastapi_app,
    socketio_path='/socket.io',
)
