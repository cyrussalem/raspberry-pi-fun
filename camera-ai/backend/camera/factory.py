import logging

from ..config import settings
from .base import Camera

logger = logging.getLogger(__name__)


def create_camera() -> Camera:
    """Create the appropriate camera instance based on configuration."""
    backend = settings.camera_backend

    if backend is None:
        # Auto-detect: try picamera2 first, fall back to opencv
        try:
            import picamera2  # noqa: F401

            backend = "picamera2"
            logger.info("Auto-detected picamera2, using Pi camera backend")
        except ImportError as e:
            backend = "opencv"
            logger.info("picamera2 not available (%s), using OpenCV webcam backend", e)
        except Exception as e:
            backend = "opencv"
            logger.warning("picamera2 import failed (%s: %s), falling back to OpenCV", type(e).__name__, e)

    if backend == "picamera2":
        from .picamera import PiCameraDevice

        return PiCameraDevice(
            width=settings.frame_width,
            height=settings.frame_height,
        )
    elif backend == "opencv":
        from .webcam import WebcamCamera

        return WebcamCamera(
            device_index=settings.camera_device_index,
            width=settings.frame_width,
            height=settings.frame_height,
        )
    else:
        raise ValueError(f"Unknown camera backend: {backend}")
