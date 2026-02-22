from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .camera.base import Camera
from .camera.factory import create_camera
from .detection.face_detector import FaceDetector
from .routers import health, video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_camera: Camera | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _camera
    # Startup
    logger.info("Initializing camera...")
    _camera = create_camera()
    _camera.open()

    detector = FaceDetector()
    video.init_video_router(_camera, detector)
    logger.info("Camera and face detector initialized")

    yield

    # Shutdown
    logger.info("Shutting down camera...")
    if _camera is not None:
        _camera.close()


app = FastAPI(title="Camera AI", lifespan=lifespan)

# CORS — needed during development when Angular runs on a separate port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(video.router)
app.include_router(health.router)

# Serve Angular static files in production
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
