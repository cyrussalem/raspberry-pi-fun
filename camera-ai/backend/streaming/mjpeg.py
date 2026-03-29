from __future__ import annotations

import logging
import threading
import time
from collections.abc import Generator

import cv2
from fastapi.responses import StreamingResponse

from ..camera.base import Camera
from ..config import settings
from ..gpio.base import GpioController
from ..recognition.base import FaceRecogniser, RecognitionResult

logger = logging.getLogger(__name__)

# Auto-unlock state
_unlock_in_progress = False
_unlock_lock = threading.Lock()
_last_unlock_times: dict[str, float] = {}


def _can_auto_unlock(name: str) -> bool:
    """Check if auto-unlock is allowed for this person (cooldown check)."""
    global _unlock_in_progress
    now = time.monotonic()
    last_time = _last_unlock_times.get(name, 0.0)
    if now - last_time < settings.recognition_cooldown:
        return False
    with _unlock_lock:
        if _unlock_in_progress:
            return False
    return True


def _trigger_auto_unlock(
    gpio: GpioController, pin: int, duration: int, name: str
) -> None:
    """Run GPIO unlock sequence in a background thread."""
    global _unlock_in_progress
    try:
        gpio.set_high(pin)
        logger.info(
            "Auto-unlock triggered for %s — GPIO pin %d HIGH", name, pin
        )
        time.sleep(duration)
    finally:
        gpio.set_low(pin)
        logger.info("Auto-unlock ended — GPIO pin %d LOW", pin)
        with _unlock_lock:
            _unlock_in_progress = False


def _handle_recognition_results(
    results: list[RecognitionResult],
    gpio: GpioController | None,
) -> None:
    """Trigger auto-unlock if a recognised staff member is detected."""
    global _unlock_in_progress
    if gpio is None:
        return

    for result in results:
        if (
            result.name != "Unknown"
            and result.confidence >= settings.recognition_threshold
            and _can_auto_unlock(result.name)
        ):
            with _unlock_lock:
                if _unlock_in_progress:
                    return
                _unlock_in_progress = True

            _last_unlock_times[result.name] = time.monotonic()
            thread = threading.Thread(
                target=_trigger_auto_unlock,
                args=(
                    gpio,
                    settings.gpio_pin,
                    settings.gpio_unlock_duration,
                    result.name,
                ),
                daemon=True,
            )
            thread.start()
            return  # Only unlock once per recognition cycle


def _draw_overlays(
    frame, results: list[RecognitionResult]
) -> None:
    """Draw bounding boxes and labels on the frame."""
    for result in results:
        x, y, w, h = result.bbox
        if result.name != "Unknown":
            color = (0, 255, 0)  # Green for known
            label = f"{result.name} ({result.confidence:.0%})"
        else:
            color = (0, 0, 255)  # Red for unknown
            label = "Unknown"

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame, label, (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
        )


def generate_frames(
    camera: Camera,
    recogniser: FaceRecogniser,
    gpio: GpioController | None = None,
) -> Generator[bytes, None, None]:
    """Generate MJPEG frames with face recognition overlays.

    Recognition runs every Nth frame (configured by recognition_every_n_frames).
    Between recognition frames, previous results are reused for overlay drawing.
    """
    frame_interval = 1.0 / settings.stream_fps
    recognition_interval = settings.recognition_every_n_frames
    frame_count = 0
    last_results: list[RecognitionResult] = []

    while True:
        start_time = time.monotonic()
        try:
            frame = camera.read_frame()
            frame_count += 1

            # Run recognition every Nth frame
            if frame_count % recognition_interval == 0:
                last_results = recogniser.recognise(frame)
                _handle_recognition_results(last_results, gpio)

            # Draw overlays from last recognition results
            _draw_overlays(frame, last_results)

            success, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
        except RuntimeError as e:
            logger.error("Frame capture error: %s", e)
            break

        # Throttle to target FPS
        elapsed = time.monotonic() - start_time
        sleep_time = frame_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


def create_mjpeg_response(
    camera: Camera,
    recogniser: FaceRecogniser,
    gpio: GpioController | None = None,
) -> StreamingResponse:
    """Create a StreamingResponse for MJPEG video."""
    return StreamingResponse(
        generate_frames(camera, recogniser, gpio),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
