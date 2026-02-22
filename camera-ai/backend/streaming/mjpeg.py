import logging
import time
from collections.abc import Generator

import cv2
from fastapi.responses import StreamingResponse

from ..camera.base import Camera
from ..config import settings
from ..detection.face_detector import FaceDetector

logger = logging.getLogger(__name__)


def generate_frames(
    camera: Camera, detector: FaceDetector
) -> Generator[bytes, None, None]:
    """Generate MJPEG frames with face detection overlays."""
    frame_interval = 1.0 / settings.stream_fps

    while True:
        start_time = time.monotonic()
        try:
            frame = camera.read_frame()
            frame = detector.detect_and_draw(frame)

            success, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
        except RuntimeError as e:
            logger.error(f"Frame capture error: {e}")
            break

        # Throttle to target FPS
        elapsed = time.monotonic() - start_time
        sleep_time = frame_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


def create_mjpeg_response(
    camera: Camera, detector: FaceDetector
) -> StreamingResponse:
    """Create a StreamingResponse for MJPEG video."""
    return StreamingResponse(
        generate_frames(camera, detector),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
