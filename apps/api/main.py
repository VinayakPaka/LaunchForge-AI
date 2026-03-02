"""LaunchForge AI — FastAPI application entry point."""
import logging
import os
import sys
import json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# ── Structured JSON logging ────────────────────────────────────────────────────
LOG_DIR = "/mnt/efs/spaces/816c522e-4986-4150-9046-877cd4d0d500/09030478-659e-4f34-8572-199ae830e8c3/logs"
os.makedirs(LOG_DIR, exist_ok=True)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        })


handler = logging.FileHandler(f"{LOG_DIR}/api.log")
handler.setFormatter(JSONFormatter())
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler, logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Rate limiter (SlowAPI — brute-force protection on auth endpoints) ──────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

from database import init_db
from routers.pipeline import router as pipeline_router
from routers.auth     import router as auth_router
from routers.images   import router as images_router
from services.auth_service import _load_or_generate_keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB tables and RSA key pair."""
    logger.info("LaunchForge AI API starting up")
    _load_or_generate_keys()          # generate RSA keys if absent
    await init_db()                   # create all DB tables
    logger.info("Database and RSA keys ready")
    yield
    logger.info("LaunchForge AI API shutting down")


app = FastAPI(
    title="LaunchForge AI API",
    description="8-agent AI pipeline: idea → launch-ready startup package",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Rate-limit state on app ────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tb314nms.run.complete.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(pipeline_router)
app.include_router(auth_router)
app.include_router(images_router)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "LaunchForge AI API", "version": "2.0.0"}


# ── Auth endpoints rate limits (applied directly via decorator in routers) ─────
# login:        5 requests/minute per IP
# register:     10 requests/minute per IP
# refresh:      30 requests/minute per IP
# All other:    200 requests/minute per IP (default)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
