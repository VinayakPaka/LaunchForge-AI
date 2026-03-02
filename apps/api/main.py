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

# Configure structured JSON logging
LOG_DIR = "/mnt/efs/spaces/816c522e-4986-4150-9046-877cd4d0d500/09030478-659e-4f34-8572-199ae830e8c3/logs"
os.makedirs(LOG_DIR, exist_ok=True)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })


handler = logging.FileHandler(f"{LOG_DIR}/api.log")
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

from database import init_db
from routers.pipeline import router as pipeline_router
from routers.auth import router as auth_router
from routers.images import router as images_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("LaunchForge AI API starting up")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("LaunchForge AI API shutting down")


app = FastAPI(
    title="LaunchForge AI API",
    description="8-agent AI pipeline: idea → launch-ready startup package",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tb314nms.run.complete.dev",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(pipeline_router)
app.include_router(auth_router)
app.include_router(images_router)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "LaunchForge AI API", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
