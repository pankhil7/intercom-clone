from contextlib import asynccontextmanager
import os
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.socket.server import sio
import app.socket.agent_namespace  # noqa: F401 — registers handlers
import app.socket.widget_namespace  # noqa: F401 — registers handlers

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", debug=settings.DEBUG, version="1.0.0")
    from app.background.scheduler import start_scheduler
    start_scheduler()
    yield
    logger.info("app_stopping")
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

from app.middleware.logging_middleware import RequestLoggingMiddleware
fastapi_app.add_middleware(RequestLoggingMiddleware)

# CORS — explicit origins required when allow_credentials=True (wildcard forbidden by spec)
_allowed_origins = list(filter(None, [settings.FRONTEND_URL, settings.WIDGET_CDN_URL]))
if settings.DEBUG:
    _allowed_origins += ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"]

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,          # required for cookies to be sent cross-origin
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
