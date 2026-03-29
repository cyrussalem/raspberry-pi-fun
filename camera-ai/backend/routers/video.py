from __future__ import annotations

from fastapi import APIRouter

from ..camera.base import Camera
from ..gpio.base import GpioController
from ..recognition.base import FaceRecogniser
from ..streaming.mjpeg import create_mjpeg_response

router = APIRouter(prefix="/api/video", tags=["video"])

_camera: Camera | None = None
_recogniser: FaceRecogniser | None = None
_gpio: GpioController | None = None


def init_video_router(
    camera: Camera,
    recogniser: FaceRecogniser,
    gpio: GpioController | None = None,
) -> None:
    global _camera, _recogniser, _gpio
    _camera = camera
    _recogniser = recogniser
    _gpio = gpio


@router.get("/stream")
async def video_stream():
    """MJPEG video stream endpoint with face recognition."""
    return create_mjpeg_response(_camera, _recogniser, _gpio)
