from __future__ import annotations

from fastapi import APIRouter

from ..camera.base import Camera
from ..detection.face_detector import FaceDetector
from ..streaming.mjpeg import create_mjpeg_response

router = APIRouter(prefix="/api/video", tags=["video"])

_camera: Camera | None = None
_detector: FaceDetector | None = None


def init_video_router(camera: Camera, detector: FaceDetector) -> None:
    global _camera, _detector
    _camera = camera
    _detector = detector


@router.get("/stream")
async def video_stream():
    """MJPEG video stream endpoint."""
    return create_mjpeg_response(_camera, _detector)
