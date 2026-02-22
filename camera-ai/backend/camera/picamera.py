import numpy as np
from numpy.typing import NDArray

from .base import Camera


class PiCameraDevice(Camera):
    """Picamera2-based camera for Raspberry Pi camera modules."""

    def __init__(self, width: int = 640, height: int = 480):
        self._width = width
        self._height = height
        self._picam2 = None

    def open(self) -> None:
        from picamera2 import Picamera2  # Deferred import — not available on Windows

        self._picam2 = Picamera2()
        config = self._picam2.create_preview_configuration(
            main={"size": (self._width, self._height), "format": "BGR888"}
        )
        self._picam2.configure(config)
        self._picam2.start()

    def read_frame(self) -> NDArray[np.uint8]:
        if self._picam2 is None:
            raise RuntimeError("Camera is not open")
        return self._picam2.capture_array()

    def close(self) -> None:
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2.close()
            self._picam2 = None
